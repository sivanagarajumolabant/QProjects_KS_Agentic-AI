# 📋 Quick Reference Card

## 📊 Data Sources
- **Sales Data**: 14 fields

## 🧮 DAX Measures
- **Profit Margin**: SUM([Profit]) / SUM([SalesAmount])...
- **Sales Category**: IF SUM([SalesAmount]) > 10000 THEN "High Sales" EL...
- **Year**: YEAR([OrderDate])...
- **Quarter**: "Q" + STR(DATEPART("quarter", [OrderDate]))...
- **Region Filter**: "All"...

## 📈 Visuals to Create
- **Sales by Region**: Scatter Chart
- **Sales Trend**: Scatter Chart
- **Category Performance**: Pie Chart
- **Profit Analysis**: Scatter Chart

## 📁 File Reference
- **DAX Measures**: `full_migration_output_measures.dax`
- **Data Connection**: `full_migration_output_data_sources.csv`
- **Sample Data**: `full_migration_output_sample_data.csv`
- **Full Guide**: `full_migration_output_PowerBI_Import_Guide.md`
