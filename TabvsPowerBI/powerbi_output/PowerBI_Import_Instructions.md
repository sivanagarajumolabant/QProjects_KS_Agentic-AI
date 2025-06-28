# Power BI Import Instructions

## Files Generated
This migration has generated the following files for Power BI:

1. **powerbi_data.csv** - Clean data ready for import
2. **powerbi_dax_script.dax** - DAX measures and calculated columns
3. **powerbi_template_structure.json** - Complete report structure
4. **PowerBI_Import_Instructions.md** - This instruction file

## Step-by-Step Import Process

### Step 1: Import Data
1. Open Power BI Desktop
2. Click "Get Data" -> "Text/CSV"
3. Select `powerbi_data.csv`
4. Click "Load"

### Step 2: Add DAX Measures
1. In the Fields pane, right-click on "Sales" table
2. Select "New measure"
3. Copy and paste each measure from `powerbi_dax_script.dax`:

```dax
Profit Margin = DIVIDE(SUM(Sales[Profit]), SUM(Sales[SalesAmount]), 0)
Total Sales = SUM(Sales[SalesAmount])
Total Profit = SUM(Sales[Profit])
Total Quantity = SUM(Sales[Quantity])
Average Order Value = DIVIDE(SUM(Sales[SalesAmount]), DISTINCTCOUNT(Sales[OrderID]), 0)
Order Count = DISTINCTCOUNT(Sales[OrderID])
Customer Count = DISTINCTCOUNT(Sales[CustomerID])
```

### Step 3: Add Calculated Columns
1. Right-click on "Sales" table
2. Select "New column"
3. Add these calculated columns:

```dax
Year = YEAR(Sales[OrderDate])
Quarter = "Q" & FORMAT(Sales[OrderDate], "Q")
```

### Step 4: Create Visuals

#### Sales by Region (Clustered Bar Chart)
- Visual: Clustered Bar Chart
- Axis: Region
- Values: Total Sales
- Sort: Descending by Total Sales

#### Sales Trend (Line Chart)
- Visual: Line Chart
- Axis: OrderDate (Month level)
- Values: Total Sales

#### Category Performance (Pie Chart)
- Visual: Pie Chart
- Legend: Category
- Values: Total Sales

#### Profit Analysis (Scatter Chart)
- Visual: Scatter Chart
- X Axis: Total Sales
- Y Axis: Total Profit
- Legend: Category
- Size: Total Quantity

### Step 5: Add Filters
1. Add slicers for:
   - Region (Dropdown style)
   - Category (List style)
   - OrderDate (Date range)

### Step 6: Format Visuals
- Apply the color schemes specified in the visual configurations
- Set appropriate titles and axis labels
- Enable cross-filtering between visuals

## Color Schemes
- **Regions**: East (#1f77b4), North (#ff7f0e), South (#2ca02c), West (#d62728)
- **Categories**: Electronics (#1f77b4), Furniture (#ff7f0e), Office Supplies (#2ca02c)

## Report Layout
- **Page 1**: Sales Dashboard (Sales by Region, Sales Trend, Category Performance)
- **Page 2**: Detailed Analysis (Profit Analysis scatter plot)

Your Tableau report has been successfully converted to Power BI!
