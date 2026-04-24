import numpy as np

def calculate_sharpe_ratio(daily_profit_rates):
    """
    Calculate Sharpe Ratio based on daily ROI changes.
    R_t = ROI_t - ROI_{t-1}
    This is less sensitive to the absolute equity level than percentage returns
    when the trader is deeply underwater.
    """
    if not daily_profit_rates or len(daily_profit_rates) < 2:
        return 0
    
    # Sort by time
    history = sorted(daily_profit_rates, key=lambda x: int(x.get('cTime', 0)))
    
    # Extract rates as decimals
    rates = [float(x.get('rate', 0)) / 100.0 for x in history]
    
    # Simple daily changes
    returns = []
    for i in range(1, len(rates)):
        daily_return = rates[i] - rates[i-1]
        returns.append(daily_return)
            
    if len(returns) < 2:
        return 0
    
    avg_return = np.mean(returns)
    std_return = np.std(returns)
    
    if std_return == 0:
        return 0
        
    # Annualized Sharpe (assuming 365 days)
    # Using simple daily average / daily std * sqrt(365)
    sharpe = (avg_return / std_return) * np.sqrt(365)
    return sharpe
