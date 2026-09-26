"""Split a sale price into its parts. Works on single values and on pandas Series.

Resale:    price = labour + materials + land and location
New build: price = labour + materials + fees and marketing + developer profit + land (no finance)
"""
import config


def split_price(price, floor_area, cost_per_m2=config.BUILD_COST_PER_M2, mode="resale") -> dict:
    if mode not in config.MODES:
        raise ValueError(f"mode must be one of {list(config.MODES)}")
    build = floor_area * cost_per_m2
    labour = build * config.LABOUR_SHARE
    if mode == "new_build":
        other = (build * config.PROFESSIONAL_FEES_SHARE_OF_BUILD
                 + price * config.MARKETING_AND_LEGAL_SHARE_OF_PRICE)
        profit = price * config.DEVELOPER_PROFIT_SHARE_OF_PRICE
    else:
        other = build * 0
        profit = price * 0
    land = price - build - other - profit
    return {
        "price": price,
        "build_cost": build,
        "labour_est": labour,
        "materials_est": build - labour,
        "other_dev_costs": other,
        "developer_profit": profit,
        "land": land,
        "land_share": land / price,
    }
