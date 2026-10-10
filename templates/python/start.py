"""Starts games of the bot from code (E120): run this file, no arguments needed.

Not part of the upload: only bot.py and data/ go to the server.
"""

import sbm
from bot import TemplateBot

# Locally against a reference bot (random, material) or another bot file.
sbm.play(TemplateBot, "material", games=2, time="60+1")

# Against a bot on the site, with the API token from your account page. Keep the token out of
# version control and out of the upload; sbm.play also reads it from SBM_TOKEN.
# sbm.play(
#     TemplateBot,
#     "Material",
#     server="https://schachbotmanager.devtgp.net",
#     token="sbm_...",
#     color="white",
#     games=2,
# )
