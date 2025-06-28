# Sample Sales Report Documentation

## Overview
This sample Tableau workbook (`sample_sales_report.twb`) demonstrates a typical sales reporting structure that our migration engine will need to handle.

## Data Source
- **Connection Type**: SQL Server
- **Database**: SalesDB
- **Server**: sql-server-01
- **Table**: [dbo].[Sales]
- **Authentication**: Windows Authentication (SSPI)

## Fields Structure

### Base Fields
| Field Name | Data Type | Role | Description |
|------------|-----------|------|-------------|
| OrderID | Integer | Dimension | Unique order identifier |
| CustomerID | String | Dimension | Customer identifier |
| ProductName | String | Dimension | Product name |
| Category | String | Dimension | Product category |
| Region | String | Dimension | Sales region |
| OrderDate | DateTime | Dimension | Order date |
| SalesAmount | Real | Measure | Sales amount in dollars |
| Quantity | Integer | Measure | Quantity sold |
| Profit | Real | Measure | Profit amount |

### Calculated Fields
1. **Profit Margin**: `SUM([Profit]) / SUM([SalesAmount])`
2. **Sales Category**: Conditional logic based on sales amount
3. **Year**: `YEAR([OrderDate])`
4. **Quarter**: `"Q" + STR(DATEPART("quarter", [OrderDate]))`

### Parameters
- **Region Filter**: List parameter with values (All, North, South, East, West)

## Worksheets

### 1. Sales by Region (Bar Chart)
- **Type**: Horizontal Bar Chart
- **Rows**: Region
- **Columns**: SUM(Sales Amount)
- **Color**: Region
- **Sort**: Descending by Sales Amount

### 2. Sales Trend (Line Chart)
- **Type**: Line Chart
- **Columns**: MONTH(Order Date)
- **Rows**: SUM(Sales Amount)
- **Color**: Blue (#1f77b4)

### 3. Category Performance (Pie Chart)
- **Type**: Pie Chart
- **Color**: Category
- **Size**: SUM(Sales Amount)
- **Categories**: Electronics, Furniture, Office Supplies

### 4. Profit Analysis (Scatter Plot)
- **Type**: Scatter Plot
- **Columns**: SUM(Sales Amount)
- **Rows**: SUM(Profit)
- **Color**: Category

## Dashboard
- **Name**: Sales Dashboard
- **Size**: 1000x800 pixels
- **Layout**: Vertical flow with nested horizontal section
- **Components**:
  - Top: Sales by Region (full width)
  - Bottom: Sales Trend and Category Performance (side by side)
- **Mobile Layout**: Vertical stack of all worksheets

## Migration Considerations

### Data Source Mapping
- SQL Server connection should map directly to Power BI SQL Server connector
- Windows Authentication should be preserved
- Table reference needs to be converted to Power BI format

### Calculation Conversion
- Tableau functions need DAX equivalents
- LOD expressions may require CALCULATE functions
- String concatenation syntax differences

### Visual Mapping
- Bar charts map directly to Power BI clustered bar charts
- Line charts map directly to Power BI line charts
- Pie charts map to Power BI pie charts
- Scatter plots map to Power BI scatter charts

### Formatting Preservation
- Color schemes should be maintained where possible
- Sort orders need to be replicated
- Axis formatting and labels
- Legend positions and formatting

This sample provides a comprehensive test case for our migration engine development.
