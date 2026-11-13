import secrets
from pathlib import Path

ROOT = Path("/root/matrix-docker")
COMPOSE = ROOT / "docker-compose.yml"
PASSWORD = ROOT / "keitaro.password"
ENV = ROOT / "keitaro.env"
MARKER = "container_name: keitaro-wrapper"


def password() -> str:
    if PASSWORD.exists():
        return PASSWORD.read_text().split()[1]
    value = secrets.token_urlsafe(12)
    PASSWORD.write_text(f"guk {value}\n")
    PASSWORD.chmod(0o600)
    return value


def env_file() -> None:
    if ENV.exists():
        return
    ENV.write_text(
        "KEITARO_BASE_URL=\nKEITARO_API_KEY=\nCAMPAIGN_PREFIX=test_guk_\n"
    )
    ENV.chmod(0o600)


def service() -> str:
    return f"""
  keitaro:
    build: ./keitaro
    image: keitaro-wrapper:local
    container_name: keitaro-wrapper
    restart: unless-stopped
    env_file:
      - ./keitaro.env
    volumes:
      - ./keitaro-data:/app/backend/data
    networks:
      - matrix
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.keitaro.rule=(Host(`alxgk.site`) || Host(`www.alxgk.site`)) && (PathPrefix(`/w/`) || Path(`/w`))"
      - "traefik.http.routers.keitaro.priority=100"
      - "traefik.http.routers.keitaro.entrypoints=websecure"
      - "traefik.http.routers.keitaro.tls=true"
      - "traefik.http.routers.keitaro.tls.certresolver=letsencrypt"
      - "traefik.http.routers.keitaro.middlewares=keitaro-slash,keitaro-robots,keitaro-strip"
      - "traefik.http.middlewares.keitaro-slash.redirectregex.regex=^(https?://[^/]+)/w$$"
      - "traefik.http.middlewares.keitaro-slash.redirectregex.replacement=$${{1}}/w/"
      - "traefik.http.middlewares.keitaro-slash.redirectregex.permanent=false"
      - "traefik.http.middlewares.keitaro-robots.headers.customresponseheaders.X-Robots-Tag=noindex, nofollow"
      - "traefik.http.middlewares.keitaro-strip.stripprefix.prefixes=/w"
      - "traefik.http.services.keitaro.loadbalancer.server.port=8000"
"""


def main() -> None:
    env_file()
    password()
    text = COMPOSE.read_text()
    if MARKER not in text:
        backup = COMPOSE.with_suffix(".yml.bak-keitaro")
        if not backup.exists():
            backup.write_text(text)
        COMPOSE.write_text(text.rstrip() + "\n" + service())
    print("ready", PASSWORD)


if __name__ == "__main__":
    main()
