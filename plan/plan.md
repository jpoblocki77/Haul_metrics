# Virtual Trucking Company Tracker (ATS / ETS2)

## What it is
A Python app with SQLite storage for running a virtual trucking company in American Truck Simulator / Euro Truck Simulator 2.
It tracks income, expenses, fuel, loads, drivers, trucks and DOT inspections, with charts. You open it in the browser after logging in.

## Who it's for
Virtual trucking company owners and managers (VTC leads) who want one place to run the company's books and see how each driver performs. US units throughout: miles, gallons, $.

## Core features and experience
- **Login**: username/password sign-in. The app comes with one owner account. Everything stays behind the login.
- **Dashboard**: totals for income, expenses and profit, plus average MPG, on-time rate and inspection results. Charts include income vs expenses over time, expenses by category, fuel cost and MPG trends, and driver comparisons.
- **Income**: log load revenue and other income with a date, driver, truck and notes.
- **Expenses**: log expenses against categories you set up yourself. Categories can be added, renamed or removed (for example Repairs, Tolls, Insurance).
- **Trucks**: add trucks by truck number and the number of gallons the tank holds. Edit or remove them later.
- **Fuel purchases**: pick a truck by its number and the gallons box fills in with that truck's tank size. You can change it for a partial fill. Enter the price per gallon and the total (gallons × price) works out automatically. Enter miles driven to get MPG for each fill-up. Average MPG is shown for each truck, each driver and the whole company, along with gallons bought.
- **Loads**: record origin, destination, driver, truck, pay and due date, and mark each load On Time or Late. On-time percentage counts toward driver performance.
- **Drivers & performance**: a list of drivers with each one's loads, revenue, miles, average MPG, on-time rate and inspection record, plus a chart comparing drivers.
- **DOT inspections**: record the date, driver, truck and location, with a result of Passed, Fined or Out of Service. Fined records have a fine amount and a reason field. You can filter by result and see totals by reason.
- **Test data**: one button adds a realistic set of sample trucks, drivers, loads, fuel, expenses and inspections. Another removes only that sample data, so your real records are never touched.

## Phase 1: what gets built now
- A browser-based app with a Python backend and SQLite. You chose both desktop and web; Phase 1 is the web version and runs in a normal browser window. Turning it into a standalone desktop window can come later.
- Owner login with username and password.
- Everything listed under Core features: dashboard and charts, income, expenses with your own categories, trucks, fuel with auto-fill and auto-calculation, MPG tracking, loads with On Time/Late, driver performance, DOT inspections with result and fine reason, and adding/removing test data.
