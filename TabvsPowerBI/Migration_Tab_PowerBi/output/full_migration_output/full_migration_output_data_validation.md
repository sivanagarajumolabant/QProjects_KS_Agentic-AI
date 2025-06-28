# Data Validation Report

## Sample Data File: sample_sales_data.csv
## Records: 30 rows

## Field Validation

| Tableau Field | Sample Data Column | Data Type Match | Status |
|---------------|-------------------|-----------------|--------|
| OrderID | OrderID | integer → int64 | ✅ Match |
| CustomerID | CustomerID | string → object | ✅ Match |
| ProductName | ProductName | string → object | ✅ Match |
| Category | Category | string → object | ✅ Match |
| Region | Region | string → object | ✅ Match |
| OrderDate | OrderDate | datetime → object | ✅ Match |
| SalesAmount | SalesAmount | real → float64 | ✅ Match |
| Quantity | Quantity | integer → int64 | ✅ Match |
| Profit | Profit | real → float64 | ✅ Match |
| Calculation_001 | Missing | real | ❌ Not Found |
| Calculation_002 | Missing | string | ❌ Not Found |
| Calculation_003 | Missing | integer | ❌ Not Found |
| Calculation_004 | Missing | string | ❌ Not Found |
| Parameter 1 | Missing | string | ❌ Not Found |

## Data Quality Summary
- **Total Records**: 30
- **Columns**: 9
- **Missing Values**: 0
- **Duplicate Rows**: 0

## Sample Data Preview
```
   OrderID CustomerID          ProductName         Category Region   OrderDate  SalesAmount  Quantity  Profit
0     1001    CUST001        Laptop Pro 15      Electronics  North  2023-01-15      1299.99         1  389.99
1     1002    CUST002  Office Chair Deluxe        Furniture  South  2023-01-16       299.99         2   89.99
2     1003    CUST003       Wireless Mouse      Electronics   East  2023-01-17        49.99         3   19.99
3     1004    CUST004       Desk Organizer  Office Supplies   West  2023-01-18        24.99         1    9.99
4     1005    CUST005      Monitor 27 inch      Electronics  North  2023-01-19       399.99         1  119.99
```
