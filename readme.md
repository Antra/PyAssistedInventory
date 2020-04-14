# Py Assisted Inventory
Py Assisted Inventory, or PAI, is a small setup to keep track of groceries, freezer contents, etc.  
A basic inventory management system for a household.  

# Usage
Works via a basic CLI menu.
- 1: Add/update items; such as adjusting minimum limits, or creating new items
- 2: List/update stock; such as listing expired/deficit items, or adding/removing from stock


# Logging
There's basic logging done in the `logs` folder.  
Log files will rotate at 256kb, and up to 10 log files are kept.

Log level can be specified with environmental variable `LOG_LEVEL`.  
Possible values are: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`, defaults to `INFO`.

# Config files
The system uses a few different configuration files to get up and running.

## ENV variables
Use either ENV variables or a .env with `dotenv.load_dotenv` to populate `SQLALCHEMY_DATABASE_URI` with the database location.  
For example, a basic sqlite db named `inventory.db` would be: `SQLALCHEMY_DATABASE_URI=sqlite:///inventory.db`.

Used values:
- SQLALCHEMY_DATABASE_URI
- LOG_LEVEL

## Base data (default_values.json)
The `db_init()` function reads `default_values.json`.  
It is expected to be a JSON with `Itemgroups`, `Containertypes`, and `Locations`, see the sample file.

## Item defaults
`_quick_init()` can be used to read a `raw_data.json`.  
It is expected to be a JSON with the item data in the various itemgroups (NB, group *must* expist already!), see the sample file.