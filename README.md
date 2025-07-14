# Option Greeks Plotting
A CLI python app and a webserver that can load and plot exposure of different greeks of any ticker using live data and show it on a Discord bot and a website.

To run the script write your discord bot token, if you want to use the webserver, and also your Tastytrade username and password in the .env file. In _discord_send_plots.py_ modify **DISCORD_CHANNEL_IDS** codes with the channel IDs in your server.

Then run:
```
python -m venv venv
:: powershell
.\venv\Scripts\Activate.ps1
:: linux
source venv/bin/activate

pip install -r requirements.txt
```
```
python webserver.py
```
Or
```
python cli-app.py
```


