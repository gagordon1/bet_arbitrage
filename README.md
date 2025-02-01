TODO:
Add descriptions to markets so llm can more precisely tell semantic equivalence given pricing is not a constraint
Make pricing orderbook aware to get most actionable trades
Automate system:

Daily script:
    Scrape both markets for semantically equivalent markets
        Every minute refresh price data
        If an orderbook aware opportunity meets some annualized return threshold execute trade on both platforms
        Return calculation should factor in trading fees on both platforms
