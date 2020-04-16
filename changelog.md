# Changelog
This will serve both as a wishlist and as a list of what I have already completed.


# Todo
- add item with barcode (NB, item may exist even if barcode doesn't! -- better to not allow and to associate barcodes later?)
- associate barcode to item
- update '_quick_init()' (similar to 'raw_data.json') to do a quick update of the stock counts (needs to do a file-rename to avoid doing over and over?)
- add proper tests instead of the debug functions
- **BUG:** _quick_init is sometimes not updating the values of existing items (e.g. minimum counts) -- fix via the item_status instead?
- Add an Admin submenu to do item import/export, initial setup (_quick_init) etc?
- Move default/data files to a subfolder?

## Other thoughts
- instead of exposing storage rows, do I want to always just show items with count? ('list_items_with_stock_count' instead of 'list_stock')
- full stock re-count/verification mode
- work with barcodes (when the barcode reader arrives ;))
- integrate via Microsoft Graph API to update Microsoft To-Do tasks (at least for shopping, also to maintain minimum limits and items? - i.e. as an "outsourced" database)
- use expiration dates for something useful
- prevent over-empty from stock? For now trusting the human knows better how much is in stock (i.e. forgot to add/remove items earlier)
- make a graphical UI
- Can I use decorators for something (better input validation and/or logging?)
- Should I keep removing the zero rows from the DB or will it be nice to keep track of how much is used of what?

# Version history
## 0.0.2
- bug fixes to the deficit counter (was counting storage rows instead of stored portions)
- added a dump of current items with current stock levels ('_item_export')
- added an adhoc import ('_item_import') to mass-update existing items (reads the file produced by the export above)

## 0.0.1
- add item
- get item
- get item by item group
- add/update minimum limit to item
- remove minimum limit from item
- add item to stock
- add item to stock with expiry date
- get list of items in stock
- get list of expired items in stock
- get list of items with minimum limits
- add function to prune StorageDB; clean-out rows with 0 or lower number of portions
- remove item from stock