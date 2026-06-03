### 1. Fixing the Weekly Demand Calculation

  The Bug: In  analysis.py  (lines 85-90 and 472-478), the weekly demand is calculated by grouping shipments by week and then
  using pandas  .unstack(fill_value=0) .
  The Issue: This only creates column headers for weeks where at least one product was sold. If there is an entire week with
  absolutely no sales across the dataset (e.g., a holiday week), that week is silently excluded. As a result,  .mean(axis=1)
  and  .std(axis=1)  will calculate the averages using a smaller denominator, artificially inflating the weekly mean demand!
  The Fix: We need to explicitly  .reindex()  the columns using a  pd.period_range  that strictly spans the 26/27 weeks of the
  Assignment Window to guarantee that completely empty weeks are padded with zeros.

  ### 2. Addressing Regional Order Double-Counting

  The Bug: In  build_warehouse_imbalance_summary  (line 370),  region_orders  is calculated by summing the order counts of the
  individual warehouses:  summary.groupby("region")["orders"].transform("sum") .
  The Issue: If a single customer order contains SKUs fulfilled from both My Phuoc and Vinh Loc, it is correctly counted as 1
  order for My Phuoc and 1 order for Vinh Loc. However, when we sum those together for the region, it double-counts the order
  as 2!
  The Fix: We need to calculate the true unique  order_id  count for each region directly from the raw  known  DataFrame
  (ignoring the warehouse split) and merge it back into the summary.

  ### 3. Fixing the Orphaned Safety Stock Logic

  The Bug: You have a complete, well-written function called  build_safety_stock_class_a()  on line 470 of  analysis.py .
  The Issue: It is completely orphaned! It is never imported into  run_analysis.py  and is never actually executed during the
  pipeline.
  The Fix: We need to invoke this function in  run_analysis.py , pass it the processed shipments and the  abc_xyz
  classification dataframe, and save its output (e.g.,  outputs/round2/safety_stock_class_a.csv ).