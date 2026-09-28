INDICATORS = {
    "gdp": {"code": "NY.GDP.MKTP.CD", "name": "GDP", "unit": "Current US$"},
    "gdp_growth": {"code": "NY.GDP.MKTP.KD.ZG", "name": "GDP Growth", "unit": "%"},
    "inflation": {"code": "FP.CPI.TOTL.ZG", "name": "Inflation", "unit": "%"},
    "unemployment": {"code": "SL.UEM.TOTL.ZS", "name": "Unemployment", "unit": "%"},
    "investment": {"code": "NE.GDI.TOTL.ZS", "name": "Gross Capital Formation", "unit": "% of GDP"},
    "fdi": {"code": "BX.KLT.DINV.WD.GD.ZS", "name": "Foreign Direct Investment", "unit": "% of GDP"},
    "government_consumption": {"code": "NE.CON.GOVT.ZS", "name": "Government Consumption", "unit": "% of GDP"},
    "household_consumption": {"code": "NE.CON.PRVT.ZS", "name": "Household Consumption", "unit": "% of GDP"},
    "exports": {"code": "NE.EXP.GNFS.ZS", "name": "Exports", "unit": "% of GDP"},
    "imports": {"code": "NE.IMP.GNFS.ZS", "name": "Imports", "unit": "% of GDP"},
    # Transparent proxy for the project-level household-income outcome.
    "household_income": {"code": "NY.ADJ.NNTY.PC.CD", "name": "Household Income Proxy (Adjusted Net National Income per Capita)", "unit": "Current US$ per capita", "proxy": True},
    # Sector structure indicators used by the sector comparison API.
    "agriculture_value_added": {"code": "NV.AGR.TOTL.ZS", "name": "Agriculture Value Added", "unit": "% of GDP"},
    "industry_value_added": {"code": "NV.IND.TOTL.ZS", "name": "Industry Value Added", "unit": "% of GDP"},
    "manufacturing_value_added": {"code": "NV.IND.MANF.ZS", "name": "Manufacturing Value Added", "unit": "% of GDP"},
    "services_value_added": {"code": "NV.SRV.TOTL.ZS", "name": "Services Value Added", "unit": "% of GDP"},
}
