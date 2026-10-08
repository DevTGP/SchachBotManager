"""Transport remote: a bot on the author's machine against a bot on the server (E116).

The SDK asks the web API for a game with an API token, joins the seat over the gateway's
WebSocket (gateway-v1) and then speaks the bot protocol v1 as over stdio. Only the standard
library is used, so the SDK keeps no dependencies.
"""
