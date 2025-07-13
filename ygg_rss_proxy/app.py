from flask import Flask, request, jsonify, Response
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from timeout_decorator import TimeoutError
from ygg_rss_proxy.rss import get_rss_feed, replace_torrent_links
from ygg_rss_proxy.settings import settings
from ygg_rss_proxy.logging_config import logger
from ygg_rss_proxy.torrent import dwl_torrent
from ygg_rss_proxy.session_manager import (
    save_session,
    get_session,
    new_session,
    init_session,
)
import requests
from requests.exceptions import RequestException, ConnectionError, Timeout

app = Flask(__name__)

app.config["SESSION_TYPE"] = "sqlalchemy"
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{settings.db_path}"
app.config["SESSION_SQLALCHEMY_TABLE"] = "sessions"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True
app.config["SESSION_KEY_PREFIX"] = "session:"
app.config["SECRET_KEY"] = settings.secret_key
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "connect_args": {"timeout": settings.db_timeout}
}

db = SQLAlchemy(app)
app.config["SESSION_SQLALCHEMY"] = db


Session(app)


@app.before_request
def before_request():
    init_session()


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint that tests connectivity to FlareSolverr and internet"""
    health_status = {
        "status": "healthy",
        "checks": {
            "flaresolverr": {"status": "unknown", "message": ""},
            "internet": {"status": "unknown", "message": ""},
            "ygg": {"status": "unknown", "message": ""}
        }
    }
    
    overall_healthy = True
    
    # Test FlareSolverr connectivity
    try:
        from ygg_rss_proxy.fspy import FlareSolverr
        
        flaresolverr_url = f"{settings.flaresolverr_shema}://{settings.flaresolverr_host}:{settings.flaresolverr_port}"
        logger.info(f"Testing FlareSolverr connectivity to {flaresolverr_url}")
        
        fs_solver = FlareSolverr(
            host=settings.flaresolverr_host,
            port=settings.flaresolverr_port,
            http_schema=settings.flaresolverr_shema,
            v="v1",
        )
        
        if fs_solver.version:
            health_status["checks"]["flaresolverr"] = {
                "status": "healthy",
                "message": f"Connected, version: {fs_solver.version}",
                "user_agent": fs_solver.user_agent
            }
            logger.info(f"✅ FlareSolverr healthy: {fs_solver.version}")
        else:
            health_status["checks"]["flaresolverr"] = {
                "status": "unhealthy", 
                "message": "Connected but no version info"
            }
            overall_healthy = False
            logger.warning("⚠️ FlareSolverr connected but no version")
            
    except Exception as e:
        health_status["checks"]["flaresolverr"] = {
            "status": "unhealthy",
            "message": f"Connection failed: {str(e)}"
        }
        overall_healthy = False
        logger.error(f"❌ FlareSolverr connection failed: {e}")
    
    # Test internet connectivity
    try:
        logger.info("Testing internet connectivity")
        response = requests.get("https://httpbin.org/ip", timeout=10)
        if response.status_code == 200:
            ip_info = response.json()
            health_status["checks"]["internet"] = {
                "status": "healthy",
                "message": f"Connected, IP: {ip_info.get('origin', 'unknown')}"
            }
            logger.info(f"✅ Internet healthy: {ip_info.get('origin', 'unknown')}")
        else:
            health_status["checks"]["internet"] = {
                "status": "unhealthy",
                "message": f"HTTP {response.status_code}"
            }
            overall_healthy = False
            logger.warning(f"⚠️ Internet connectivity issue: HTTP {response.status_code}")
    except Exception as e:
        health_status["checks"]["internet"] = {
            "status": "unhealthy",
            "message": f"Connection failed: {str(e)}"
        }
        overall_healthy = False
        logger.error(f"❌ Internet connectivity failed: {e}")
    
    # Test YGG connectivity
    try:
        logger.info(f"Testing YGG connectivity to {settings.ygg_url}")
        response = requests.head(settings.ygg_url, timeout=10, allow_redirects=True)
        if response.status_code in [200, 403]:  # 403 is expected from Cloudflare
            health_status["checks"]["ygg"] = {
                "status": "healthy",
                "message": f"Reachable (HTTP {response.status_code})"
            }
            logger.info(f"✅ YGG reachable: HTTP {response.status_code}")
        else:
            health_status["checks"]["ygg"] = {
                "status": "degraded",
                "message": f"Unexpected status: HTTP {response.status_code}"
            }
            logger.warning(f"⚠️ YGG unexpected status: HTTP {response.status_code}")
    except Exception as e:
        health_status["checks"]["ygg"] = {
            "status": "unhealthy",
            "message": f"Connection failed: {str(e)}"
        }
        overall_healthy = False
        logger.error(f"❌ YGG connectivity failed: {e}")
    
    # Set overall status
    if not overall_healthy:
        health_status["status"] = "degraded"
    
    status_code = 200 if overall_healthy else 503
    logger.info(f"Health check completed: {health_status['status']}")
    
    return jsonify(health_status), status_code


@app.route("/rss", methods=["GET"])
def proxy_rss():
    """Proxy RSS feed requests to YGG with proper error handling"""
    query_params = request.query_string.decode("utf-8")
    logger.info(f"RSS request received with {len(query_params)} chars of parameters")
    
    try:
        ygg_session = get_session()
        response = None
        
        # First attempt
        try:
            logger.debug("Making initial RSS request to YGG")
            response = get_rss_feed(query_params, requests_session=ygg_session)
            logger.debug(f"Initial RSS response: HTTP {response.status_code}")
            
        except TimeoutError as e:
            logger.error(f"RSS request timeout: {e}")
            return jsonify({"error": "Request timeout", "details": "YGG request timed out"}), 504
        except (ConnectionError, RequestException) as e:
            logger.error(f"RSS request connection error: {e}")
            return jsonify({"error": "Connection failed", "details": "Could not connect to YGG"}), 502
        except Exception as e:
            logger.error(f"RSS request unexpected error: {e}")
            return jsonify({"error": "Internal error", "details": "Unexpected error during YGG request"}), 500

        # Handle authentication issues and retry
        if response.status_code in [401, 403, 307, 301]:
            logger.info(f"Authentication issue detected (HTTP {response.status_code}), re-authenticating...")
            
            try:
                ygg_session = new_session()
                logger.debug("Re-authentication successful, retrying RSS request")
                response = get_rss_feed(query_params, requests_session=ygg_session)
                logger.debug(f"Retry RSS response: HTTP {response.status_code}")
                
            except TimeoutError as e:
                logger.error(f"RSS retry request timeout: {e}")
                return jsonify({"error": "Retry timeout", "details": "YGG retry request timed out"}), 504
            except (ConnectionError, RequestException) as e:
                logger.error(f"RSS retry connection error: {e}")
                return jsonify({"error": "Retry failed", "details": "Could not reconnect to YGG"}), 502
            except Exception as e:
                logger.error(f"RSS retry unexpected error: {e}")
                return jsonify({"error": "Retry error", "details": "Error during re-authentication or retry"}), 500

        # Process successful response
        if response.status_code == 200:
            logger.info("RSS request successful, processing feed")
            try:
                save_session(ygg_session)
                modified_rss = replace_torrent_links(response.content)
                logger.info("RSS feed processed and links replaced successfully")
                return Response(modified_rss, content_type="application/xml; charset=utf-8")
            except Exception as e:
                logger.error(f"RSS processing error: {e}")
                return jsonify({"error": "Processing failed", "details": "Error processing RSS feed"}), 500
        else:
            logger.warning(f"RSS request failed with HTTP {response.status_code}")
            return jsonify({
                "error": "YGG request failed", 
                "details": f"YGG returned HTTP {response.status_code}"
            }), response.status_code

    except Exception as e:
        logger.error(f"Unexpected RSS route error: {e}")
        return jsonify({"error": "Internal error", "details": "Unexpected server error"}), 500


@app.route("/torrent", methods=["GET"])
def proxy_torrent():
    """Proxy torrent download requests to YGG with proper error handling"""
    query_params = request.query_string.decode("utf-8")
    logger.info(f"Torrent request received with {len(query_params)} chars of parameters")
    
    try:
        ygg_session = get_session()
        response = None
        
        # First attempt
        try:
            logger.debug("Making initial torrent request to YGG")
            response = dwl_torrent(query_params, requests_session=ygg_session)
            logger.debug(f"Initial torrent response: HTTP {response.status_code}")
            
        except TimeoutError as e:
            logger.error(f"Torrent request timeout: {e}")
            return jsonify({"error": "Request timeout", "details": "YGG torrent request timed out"}), 504
        except (ConnectionError, RequestException) as e:
            logger.error(f"Torrent request connection error: {e}")
            return jsonify({"error": "Connection failed", "details": "Could not connect to YGG for torrent"}), 502
        except Exception as e:
            logger.error(f"Torrent request unexpected error: {e}")
            return jsonify({"error": "Internal error", "details": "Unexpected error during torrent request"}), 500

        # Handle authentication issues and retry
        if response.status_code in [401, 403, 307, 301]:
            logger.info(f"Authentication issue detected (HTTP {response.status_code}), re-authenticating...")
            
            try:
                ygg_session = new_session()
                logger.debug("Re-authentication successful, retrying torrent request")
                response = dwl_torrent(query_params, requests_session=ygg_session)
                logger.debug(f"Retry torrent response: HTTP {response.status_code}")
                
            except TimeoutError as e:
                logger.error(f"Torrent retry request timeout: {e}")
                return jsonify({"error": "Retry timeout", "details": "YGG torrent retry timed out"}), 504
            except (ConnectionError, RequestException) as e:
                logger.error(f"Torrent retry connection error: {e}")
                return jsonify({"error": "Retry failed", "details": "Could not reconnect to YGG for torrent"}), 502
            except Exception as e:
                logger.error(f"Torrent retry unexpected error: {e}")
                return jsonify({"error": "Retry error", "details": "Error during torrent re-authentication"}), 500

        # Process successful response
        if response.status_code == 200:
            logger.info("Torrent request successful")
            try:
                save_session(ygg_session)
                logger.info("Torrent file served successfully")
                return Response(response.content, content_type="application/x-bittorrent")
            except Exception as e:
                logger.error(f"Torrent session save error: {e}")
                return jsonify({"error": "Session error", "details": "Error saving session after torrent"}), 500
        else:
            logger.warning(f"Torrent request failed with HTTP {response.status_code}")
            return jsonify({
                "error": "YGG torrent failed", 
                "details": f"YGG returned HTTP {response.status_code}"
            }), response.status_code

    except Exception as e:
        logger.error(f"Unexpected torrent route error: {e}")
        return jsonify({"error": "Internal error", "details": "Unexpected server error"}), 500


if __name__ == "__main__":
    app.run(host=settings.dev_host, port=settings.dev_port, debug=settings.debug)
