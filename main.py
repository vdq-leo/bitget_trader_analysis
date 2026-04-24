import pandas as pd
import webbrowser
import os
import time
import numpy as np
import argparse
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from bitget_trader_analysis.api_client import BitgetAPIClient
from bitget_trader_analysis.analyzer import calculate_sharpe_ratio
from bitget_trader_analysis.config import DEFAULT_LIMIT
from bitget_trader_analysis.dashboard import generate_dashboard

console = Console()

def calculate_30d_mdd(history):
    if not history: return 0
    sorted_hist = sorted(history, key=lambda x: int(x.get('cTime', 0)))
    rates = [float(h.get('rate', 0)) for h in sorted_hist]
    peak = -float('inf')
    max_dd = 0
    for r in rates:
        if r > peak: peak = r
        dd = peak - r
        if dd > max_dd: max_dd = dd
    return max_dd

def create_table(results):
    table = Table(title="Bitget Elite Trader Dashboard", header_style="bold magenta", border_style="blue")
    table.add_column("Rank", justify="right", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Sharpe (30D)", justify="right")
    table.add_column("ROI (30D)", justify="right")
    table.add_column("ROI (Life)", justify="right")
    table.add_column("Total Profit", justify="right", style="yellow")
    table.add_column("MDD (Life)", justify="right", style="red")
    table.add_column("Days", justify="right", style="blue")
    table.add_column("Copiers", justify="right", style="magenta")

    sorted_results = sorted(results, key=lambda x: x["sharpeRatio"], reverse=True)
    for i, r in enumerate(sorted_results[:25]):
        sharpe_color = "green" if r["sharpeRatio"] > 1.5 else ("yellow" if r["sharpeRatio"] > 0.5 else "red")
        roi_30_color = "green" if r["roi_30d"] > 0 else "red"
        roi_life_color = "green" if r["roi"] > 0 else "red"
        
        table.add_row(
            str(i + 1),
            r["traderName"],
            f"[{sharpe_color}]{r['sharpeRatio']:.3f}[/{sharpe_color}]",
            f"[{roi_30_color}]{r['roi_30d']:.2f}%[/{roi_30_color}]",
            f"[{roi_life_color}]{r['roi']:.2f}%[/{roi_life_color}]",
            r["totalProfit"],
            f"{r['mdd_life']:.2f}%",
            str(r["tradeDays"]),
            str(r["followCount"])
        )
    return table

def run_analysis(limit=DEFAULT_LIMIT):
    client = BitgetAPIClient()
    
    console.print(f"[bold blue]Fetching top {limit} traders from Bitget...[/bold blue]")
    traders = client.get_all_traders(limit=limit)
    console.print(f"[green]Found {len(traders)} traders.[/green]\n")
    
    if not traders:
        console.print("[bold red]No traders found.[/bold red]")
        return

    results = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Calculating risk metrics...", total=len(traders))
        
        for i, t in enumerate(traders):
            trader_id = t.get("traderId")
            trader_name = t.get("traderName") or t.get("nickName") or "Unknown"
            
            try:
                # 1. Performance History
                profit_rates = t.get("dailyProfitRateList", [])
                sharpe_30d = calculate_sharpe_ratio(profit_rates)
                mdd_30d = calculate_30d_mdd(profit_rates)
                
                # 2. ROI (30D)
                roi_30d = 0
                if profit_rates and len(profit_rates) > 1:
                    hist = sorted(profit_rates, key=lambda x: int(x.get('cTime', 0)))
                    roi_30d = float(hist[-1].get('rate', 0)) - float(hist[0].get('rate', 0))
                
                # 3. Stats from columns
                roi_life = 0
                total_profit = "$0"
                columns = t.get("columnList", [])
                for col in columns:
                    desc = col.get("describe", "")
                    val = col.get("value", "0")
                    if desc == "ROI":
                        roi_life = float(val.replace("%", "").replace(",", ""))
                    elif desc == "Total PnL":
                        total_profit = val
                
                # 4. Risk & Meta
                mdd_life = float(t.get("maxCallbackRate", 0))
                open_positions = t.get("currentTradingList", [])
                trade_days = int(t.get("tradeDays", 0))
                follow_count = int(t.get("followCount", 0))
                
                results.append({
                    "traderName": trader_name,
                    "traderId": trader_id,
                    "sharpeRatio": sharpe_30d,
                    "roi": roi_life,
                    "roi_30d": roi_30d,
                    "totalProfit": total_profit,
                    "mdd_30d": mdd_30d,
                    "mdd_life": mdd_life,
                    "tradeDays": trade_days,
                    "followCount": follow_count,
                    "openPositions": open_positions,
                    "roiHistory": profit_rates
                })
                
                progress.update(task, advance=1)
                
            except Exception as e:
                progress.update(task, advance=1)
                continue
            
    if not results:
        console.print("[bold red]No results generated.[/bold red]")
        return

    # Final Display
    console.print(create_table(results))
    
    # Generate Interactive Dashboard
    dashboard_path = generate_dashboard(results)
    console.print(f"[bold cyan]Interactive dashboard ready at: {dashboard_path}[/bold cyan]")
    
    try:
        webbrowser.open(f"file://{dashboard_path}")
    except:
        pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bitget Trader Analysis Tool")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help="Number of traders to analyze")
    args = parser.parse_args()
    run_analysis(limit=args.limit)
