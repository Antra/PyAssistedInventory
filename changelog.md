# Changelog
This will serve both as a wishlist and as a list of what I have already completed.


# Todo
- add item with barcode (NB, item may exist even if barcode doesn't! -- better to not allow and to associate barcodes later?)
- associate barcode to item
- update '_quick_init()' (similar to 'raw_data.json') to do a quick update of the stock counts (needs to do a file-rename to avoid doing over and over?)
- add proper tests instead of the debug functions

## Other thoughts
- full stock re-count/verification mode
- work with barcodes (when the barcode reader arrives ;))
- integrate via Microsoft Graph API to update Microsoft To-Do tasks (at least for shopping, also to maintain minimum limits and items? - i.e. as an "outsourced" database)
- use expiration dates for something useful
- prevent over-empty from stock? For now trusting the human knows better how much is in stock (i.e. forgot to add/remove items earlier)
- make a graphical UI
- Can I use decorators for something (better input validation?)
- Should I keep removing the zero rows from the DB or will it be nice to keep track of how much is used of what?

# Version history
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