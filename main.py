import os
import sys
import logging
from logging.handlers import RotatingFileHandler
import json
from dotenv import load_dotenv
import sqlalchemy as db
from sqlalchemy import func
from sqlalchemy.sql.functions import coalesce
from sqlalchemy.orm import sessionmaker
from models import Base, Item, Storage, Barcode, ItemGroup, ContainerType, Location, _create
import datetime as dt

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))
Session = sessionmaker()


# TODO:
# add item with barcode (NB, item may exist even if barcode doesn't! -- better to not allow and to associate barcodes later?)
# associate barcode to item

# Done:
# add item
# get item
# get item by item group
# add/update minimum limit to item
# remove minimum limit from item
# add item to stock
# add item to stock with expiry date
# get list of items in stock
# get list of expired items in stock
# get list of items with minimum limits
# Add function to prune StorageDB; clean-out rows with 0 or lower number of portions
# remove item from stock

def setup(basedir=''):
    '''
    Set things up for the application to run and start logging in '/logs'
    '''
    logdir = os.path.join(basedir, 'logs')
    if not os.path.exists(logdir):
        os.mkdir('logs')
    loglevel = logging.DEBUG  # NOTSET | DEBUG | INFO | WARNING | ERROR | CRITICAL
    logging.basicConfig(
        # filename=logdir + '/logfile.log',
        # filemode='a',
        format='%(asctime)s %(levelname)s: %(message)s',
        level=loglevel,
        handlers=[RotatingFileHandler(
            logdir + '/logfile.log',
            maxBytes=256000,
            backupCount=10)]
    )
    logging.info('** Program started!')


def db_init():
    '''Set the DB up, create basic tables, read default values, etc.'''
    database = os.environ.get('SQLALCHEMY_DATABASE_URI')
    if not database:
        database = 'sqlite:///:memory:'
    logging.info(f'Initialising database.')
    engine = db.create_engine(database, echo=False)
    Session.configure(bind=engine)

    # Create tables - fails silently if the table already exists.
    session = Session()
    Base.metadata.create_all(engine)  # Creates the table
    session.commit()
    _read_defaults(session, 'default_values.json')
    return session


def _read_defaults(session, file):
    '''This reads a JSON file with default values, supporting function to get default values added to the DB'''
    logging.info('Importing default values')
    with open(file, encoding='utf-8') as json_file:
        data = json.load(json_file)
        # ItemGroup
        for itemgroup in data['itemgroups']:
            result = _create(session, ItemGroup, name=itemgroup.capitalize())
            logging.debug(
                f"Itemgroup '{itemgroup}' created? {result[1]} - {result[0]}")
        # ContainerType
        for container in data['containertypes']:
            result = _create(session, ContainerType,
                             name=container.capitalize())
            logging.debug(
                f"Containertype '{container}' created? {result[1]} - {result[0]}")
        # StorageLocation
        for location in data['locations']:
            result = _create(session, Location,
                             name=location.capitalize())
            logging.debug(
                f"Storagelocation '{location}' created? {result[1]} - {result[0]}")
        session.commit()


def clear_screen():
    # for windows
    if os.name == 'nt':
        return os.system('cls')
    # for mac and linux(here, os.name is 'posix')
    else:
        return os.system('clear')


def pause():
    '''Pauses by asking the user for input, accepts anything'''
    return get_input_str("Press <Enter> to resume:", accept_blank=True)


def _quick_init(session, file):
    '''This reads a JSON file, supporting function to get default values added to the DB'''
    with open(file, encoding='utf-8') as json_file:
        data = json.load(json_file)
        for group in data.keys():
            group_id = session.query(ItemGroup.id).filter(
                func.upper(ItemGroup.name) == group.upper()).scalar()
            for item in data[group]:
                type_id = None
                if item.get('container_type'):
                    type_id = session.query(ContainerType.id).filter(
                        func.upper(ContainerType.name) == item['container_type'].upper()).scalar()
                new_item = Item(name=item['name_en'],
                                name_dk=item['name_da'],
                                min_limit=item['minimum_limit'],
                                group_id=group_id,
                                type_id=type_id,
                                standard_duration=item.get('standard_duration', None))
                session.add(new_item)
        session.commit()


def teardown(session):
    '''Close the setup gracefully'''
    session.close()
    logging.info('** Program closing down!')


def add_item(session, name, group, item_id=None, **kwargs):
    '''Create a new item or update existing one

    NB, non-existing parameters (columns) will result in an error!

    Parameters:
        name (str): The name of the item
        group (str): The name of the item group
        item_id (int): The ID of the item, in case of an update (optional)

    Others:
        container (str): The name of the container type (e.g. Can or Frozen)
        barcode (str): A barcode that identifies this item
        min_limit (int): The minimum limit to have in stock
        standard_duration (int): The number of days before the item expires

    Returns:
        obj: The created or updated item
    '''
    # find the group
    # find the container
    # check if the item already exists, by id or name
    # associate the barcode to the item (get_or_create)
    # add the item (get_or_create)
    # specify min_limit to the item (get_or_create)
    # specify the standard duration to the item (get_or_create)
    # return the item with all associated data

    if not session:
        return None

    # Find the group
    group_id = session.query(ItemGroup.id).filter(
        func.upper(ItemGroup.name) == group.upper()).scalar()

    # Find the container if given
    container = kwargs.pop('container', None)
    if container:
        type_id = session.query(ContainerType.id).filter(func.upper(
            ContainerType.name) == container.upper()).scalar()
    else:
        type_id = None

    # Check if the item already exists, either by ID or Name
    if item_id:
        item = session.query(Item).filter(Item.id == item_id).first()
    else:
        item = session.query(Item).filter(
            func.upper(Item.name) == name.upper()).first()
        if item:
            item_id = item.id

    # Associate barcode
    barcode_id = kwargs.pop('barcode', None)
    # TODO: Get_or_create the barcode and barcode_id and then associate it to the item

    # Create new item
    result = _create(session, Item, name=name.capitalize(),
                     group_id=group_id, type_id=type_id, id=item_id, ** kwargs)
    logging.debug(
        f"Item '{name}' created? {result[1]} - {result[0]}")
    session.flush()

    barcode = None
    standard_duration = None

    if kwargs.get('min_limit', ''):
        result[0].set_min(kwargs['min_limit'])

    if kwargs.get('standard_duration', ''):
        result[0].set_std_dur(kwargs['standard_duration'])

    session.commit()
    return result


def add_to_stock(session, item_id, location_id, portions, expiration_date=None):
    '''Helper method to put items in stock'''
    storage_date = dt.datetime.today().date()
    item = _create(session, Item, id=item_id)[0]
    if expiration_date is not None:
        expiry_date = expiration_date
    elif item.get_std_dur() is not None:
        expiry_date = (dt.datetime.today() + dt.timedelta(item.get_std_dur())
                       ).date()
    else:
        expiry_date = get_input_str("What is the expiry date? (YYYY-MM-DD or Blank for none)",
                                    valid_date=True, accept_blank=True)
        if expiry_date == '':
            expiry_date = None
    result = _create(session, Storage, item_id=item_id, storage_date=storage_date,
                     expiration_date=expiry_date, portions=portions, location_id=location_id)
    session.commit()
    logging.info(f"Storage updated: {result}")
    return result


def list_items(session, model):
    '''Generator that yields the items of type model'''

    results = session.query(model).all()
    for row in results:
        yield row


def _get_items_by_group(session, group_id):
    results = session.query(Item).filter(Item.group_id == group_id).all()
    for row in results:
        yield row


def _purge_zero_stock(session):
    '''Prune the zero items from the stock'''
    result = session.query(Storage).filter(Storage.portions == 0).delete()
    logging.info(
        f"Database clean-up. Clearing zero portion rows from the storage database, removed {result} rows.")
    return None


def list_stock(session, item_id=None, exclude_empty=True):
    '''Helper function list the items from the stock

    Parameter:
        item_id (int): Check only for a specific item?
        exclude_empty (boolean): Whether to exclude items with 0 or less in stock

    Returns:
        list of the storage rows
    '''

    if item_id and exclude_empty:
        storage_rows = session.query(Storage).filter(
            Storage.item_id == item_id).filter(Storage.portions > 0).all()
    elif item_id:
        storage_rows = session.query(Storage).filter(
            Storage.item_id == item_id).all()
    elif exclude_empty:
        storage_rows = session.query(Storage).filter(
            Storage.portions > 0).all()
    else:
        storage_rows = session.query(Storage).all()

    return storage_rows


def get_input_str(message, max_length=None, accept_string=None, valid_date=False, accept_blank=False):
    '''
    Helper function to request str input from the user

    Parameters:
        max_length: The maximum acceptable string length(optional)
        accept_string: The acceptable values for input(e.g. 1-char choices)(optional)
        valid_date: Only accept valid YYYY-MM-DD formatted strings(optional)
        accept_blank: Whether to accept the empty input(optional)

    Returns:
        String or '' (if accept_blank)
    '''
    message += " "
    while True:
        user_input = input(message)
        try:
            if (accept_blank and user_input == ''):
                return user_input
            if (valid_date and dt.datetime.strptime(user_input, '%Y-%m-%d')):
                return dt.datetime.strptime(user_input, '%Y-%m-%d').date()
            user_input = str(user_input)
            if (not max_length or len(user_input) <= max_length) and (not accept_string or user_input.upper() in accept_string.upper()) and user_input:
                return user_input
            else:
                print("Sorry, invalid input. Please try again.")
        except ValueError:
            print("Sorry, invalid input. Please try again.")


def get_input_int(message, lower_bound=None, upper_bound=None, acceptable_values=[], accept_blank=False):
    '''
    Helper function to request int input from the user

    Parameters:
        lower_bound: The minimum acceptable int value(optional)
        upper_bound: The maximum acceptable int value(optional)
        acceptable_values: The list of acceptable int values(optional)
        accept_blank: Whether to accept the empty input(optional)

    Returns:
        Int or None (if accept_blank)
    '''
    message += " "
    while True:
        user_input = input(message)
        try:
            if (accept_blank and user_input == ''):
                return user_input
            user_input = int(user_input)
            if lower_bound != None and upper_bound != None:
                if lower_bound <= user_input <= upper_bound:
                    return user_input
                else:
                    print("Sorry, invalid input. Please try again.")
                    continue
            if (lower_bound is not None and lower_bound <= user_input) or (upper_bound is not None and user_input <= upper_bound) and len(acceptable_values) == 0:
                return user_input
            elif (len(acceptable_values) > 0 and user_input in acceptable_values):
                return user_input
            else:
                print("Sorry, invalid input. Please try again.")
                continue
        except ValueError:
            print("Sorry, invalid input. Please try again.")


def _select_group(session):
    '''
    Helper function to get items from a group

    Returns:
        Tuple consisting of(group_id, group_name)
    '''
    print("These are the existing item groups:")
    for group in list_items(session, ItemGroup):
        max_group_id = group.id
        print(f'  {group.id}) {group.name}')

    group_id = get_input_int('Which group do you want to open?',
                             lower_bound=1, upper_bound=max_group_id)
    group_name = session.query(ItemGroup.name).filter(
        ItemGroup.id == group_id).scalar()

    return group_id, group_name


def _select_location(session):
    '''
    Helper function to select location

    Returns:
        Tuple consisting of(location_id, location_name)
    '''
    print("The available locations are:")
    for location in list_items(session, Location):
        max_location_id = location.id
        print(f'  {location.id}) {location.name}')

    location_id = get_input_int('Which location do you want to use?',
                                lower_bound=1, upper_bound=max_location_id)
    location_name = session.query(Location.name).filter(
        Location.id == location_id).scalar()

    return location_id, location_name


def interactivate_list_stock(session):
    '''The interactive session to add or remove items from stock or to list expired or deficits'''
    group_id = None
    item = None

    print("List or update stock")

    ch = get_input_str("Press 'L' to list stock contents, or 'A' to add to stock, 'R' to remove from stock. Press 'Q' to go back.",
                       max_length=1, accept_string='ALQR')

    if ch.upper() == 'A':
        # Add -- to which group?
        location_id, _ = _select_location(session)

        group_id, group_name = _select_group(session)

        print(f"These are the existing items in the '{group_name}' category:")
        valid_ids = []
        for item in _get_items_by_group(session, group_id):
            valid_ids.append(item.id)
            print(item.get_info(prefix='  ', short=True))

        item_id = get_input_int("Which item ID do you wish to add to stock? (Blank to cancel)",
                                acceptable_values=valid_ids, accept_blank=True)
        if item_id == '':
            return menu(session)

        portions = get_input_int("How many portions are you adding? (Blank to cancel)",
                                 lower_bound=1, accept_blank=True)
        if item_id in valid_ids and portions:
            result = add_to_stock(session, item_id=item_id,
                                  location_id=location_id,
                                  portions=portions)

    elif ch.upper() == 'L':
        # Listing menu
        ch = get_input_str("Press 'L' to list current contents, or 'E' to list expired contents, or 'D' to list deficits (missing). Press 'Q' to go back.",
                           max_length=1, accept_string='DELQ')

        if ch.upper() == 'D':
            # Listing deficits
            print("These are the deficits:")
            deficits = deficit_stock(session)
            if deficits:
                for item_name, item_id, number_missing in deficits:
                    print(
                        f"Item: {item_name} (id: {item_id}) is missing {number_missing} portions.")
            else:
                print("Currently no deficits - all items meet minimum limits")

            pause()

        elif ch.upper() == 'E':
            # Listing expired items
            expired = expired_stock(session)

            if expired:
                for row in expired:
                    print(row.get_row(prefix='  '))
            else:
                print("Nothing has expired yet")

            pause()

        elif ch.upper() == 'L':
            # Listing all items (omitting empty rows)
            stock_contents = list_stock(session, exclude_empty=True)
            for row in stock_contents:
                print(row.get_row(prefix='  '))

            pause()

        else:
            return menu(session)

    elif ch.upper() == 'R':
        # Remove from stock
        print("These are the items in stock:")

        stock_contents = list_stock(session, exclude_empty=True)

        valid_ids = []
        for row in stock_contents:
            valid_ids.append(row.item_id)
            print(row.get_row(prefix='  '))

        item_id = get_input_int("Which item ID do you wish to update? (Blank to cancel)",
                                acceptable_values=valid_ids, accept_blank=True)

        if item_id == '':
            return menu(session)

        # TODO: Do we want to make a check not to "over-remove" from stock? For now, I'll leave it out under the presumption that human eyes are better judges of how many items are in stock
        portions_to_remove = get_input_int("How many portions are you removing?",
                                           lower_bound=0)

        storage_rows = list_stock(session, item_id=item_id, exclude_empty=True)

        for storage_row in storage_rows:
            temp_reduction = min(storage_row.portions, portions_to_remove)
            storage_row.portions -= temp_reduction
            portions_to_remove -= temp_reduction
            logging.debug(
                f"Removing {temp_reduction} portions from Row {storage_row}")
            session.flush()

        session.commit()
        stmt = session.query(Storage.item_id, func.count(
            '*').label('stored_count')).group_by(Storage.item_id).subquery()

        updated_count = session.query(Storage).filter(
            Storage.item_id == item_id).group_by(Storage.item_id).scalar()

        print(f"Done! There are now {updated_count.portions} left!")

        pause()

        # return menu(session)

    else:
        # Quit -- back to menu
        return menu(session)

    return menu(session)


def interactive_add_update_item(session):
    '''The interactive session to create or update an item'''
    group_id = None
    item = None

    print("Add or update items")
    group_id, group_name = _select_group(session)

    clear_screen()
    print(f"These are the existing items in the '{group_name}' category:")
    valid_ids = []
    for item in _get_items_by_group(session, group_id):
        valid_ids.append(item.id)
        print(item.get_info(prefix='  '))

    ch = get_input_str("Press 'C' to create a new item or 'U' to update the limit of an item. Press 'Q' to go back.",
                       max_length=1, accept_string='CUQ')

    if ch.upper() == 'C':
        # Create
        name = get_input_str("What is the name of the item?").capitalize()
        if name:
            logging.info(f'Creating item {name} in category: \'{group_name}\'')
            item = add_item(session, name=name, group=group_name)[0]

    elif ch.upper() == 'U':
        # Update
        item_id = get_input_int("Which item ID do you wish to update? (Blank to cancel)",
                                acceptable_values=valid_ids, accept_blank=True)
        if item_id in valid_ids:
            item = _create(session, Item, id=item_id)[0]

    else:
        # Quit -- back to menu
        return menu(session)

    # Shared Create/Update steps
    clear_screen()
    print(f"Updating values for {item.name} (id: {item.id})")
    min_limit = get_input_int("Which minimum limit do you want to use? (Blank for none)",
                              lower_bound=0, accept_blank=True)
    std_duration = get_input_int("Which standard duration (in days) do you want to use? (Blank for none)",
                                 lower_bound=0, accept_blank=True)
    if min_limit:
        logging.info(f"Specifying minimum limit to {min_limit}")
        item.set_min(min_limit)
    if std_duration:
        logging.info(f"Specifying standard duration to {std_duration}")
        item.set_std_dur(std_duration)
    session.commit()
    logging.info(f"Item successfully updated! {item.get_info()}")
    print(f"Item successfully updated! {item.get_info()}")

    return menu(session)


def debug(session):
    '''This is a test method just for checking contents'''
    # TODO: Replace this with proper testing at some point

    # Query the DB, do we have items?
    results = session.query(Item).all()
    print("This is the current DB contents for items:", results)

    results = session.query(ItemGroup).all()
    print("This is the current DB contents for item groups:", results)

    results = session.query(Item).filter(Item.group_id == 7).all()
    print("This is all the items in item group 7:", results)

    results = session.query(ContainerType).all()
    print("This is the current DB contents for container types:", results)

    results = session.query(Item).filter(
        Item.name == 'Mackrel in tomato sauce').all()
    print("This is the first Item with a Container Type:", results)

    results = session.query(Item).filter(
        Item.containertype != None).all()
    print("This is all Items with a Container Type:", results)
    add_item(session, 'TestItem', group='beverages', container='bottle',
             min_limit=1, barcode=124312412, standard_duration=5)
    add_item(session, 'TestItem2', group='toppings', barcode='124312413', container='can',
             min_limit=2, standard_duration=5)
    add_item(session, 'TestItem3', group='grains', barcode='124312414')
    add_item(session, 'TestItem4', group='meat', min_limit=0,
             standard_duration=5, barcode='124312415')
    add_item(session, 'TestItem', group='beverages', container='bottle',
             min_limit=4, standard_duration=5, barcode=124312412)
    add_item(session, 'TestItem', group='beverages', container='bottle',
             min_limit=5, standard_duration=5)
    add_item(session, 'TestItem', group='beverages', item_id=47, container='bottle',
             min_limit=7, standard_duration=6)

    add_item(session, 'TestItem5', group='beverages', container='bottle',
             min_limit=5, standard_duration=6)

    add_item(session, 'TestItem', group='beverages', container='bottle',
             min_limit=5)

    results = session.query(Item).filter(Item.name == 'Testitem').all()
    print("These are all the 'TestItem' items:", results)

    results = session.query(Item).filter(Item.name.like('%TEST%')).all()
    print("These are all the TEST items:", results)

    for item in list_items(session, ItemGroup):
        print(item.name, item.id)


def debug_stock(session):
    '''This is a test method just for checking contents'''
    # TODO: Replace this with proper testing at some point

    expire = dt.date.today() + dt.timedelta(days=8)
    add_to_stock(session, 3, 2, 1, expire)
    add_to_stock(session, 21, 1, 12)
    expire = dt.date.today() + dt.timedelta(days=30)
    add_to_stock(session, 4, 3, 1, expire)
    expire = dt.date.today() - dt.timedelta(days=2)
    add_to_stock(session, 21, 1, 1, expire)
    session.flush()

    stock = list_items(session, Storage)
    for row in stock:
        print(row.get_row(prefix='  '))


def deficit_stock(session):
    '''

    Get the items that are below their minimum limits

    Parameters:
        none (other than the session)

    Returns:
        A list of tuples [(item_name, item_id, number_missing)]
    '''

    # Begin by removing any zero-rows from Storage
    _purge_zero_stock(session)

    # Next create a subquery with "stored_count" for each item
    stmt = session.query(Storage.item_id, func.count(
        '*').label('stored_count')).group_by(Storage.item_id).subquery()

    deficits = []

    # Then get all the items with their stored_counts:
    for item, count in session.query(Item, coalesce(stmt.c.stored_count, 0)).outerjoin(stmt, Item.id == stmt.c.item_id).order_by(Item.id):
        if item.min_limit > count:
            deficits.append((item.name, item.id, item.min_limit - count))
        else:
            print(f"skipping this!!!{item} - {count}")

    return deficits


def expired_stock(session):
    '''Get the items that are past their date'''
    # Begin by removing any zero-rows from Storage
    _purge_zero_stock(session)

    today = dt.date.today()

    results = session.query(Storage).filter(
        Storage.expiration_date < today).filter(Storage.portions > 0).all()

    return results


def exec_menu(session, choice, menu_actions):
    clear_screen()
    ch = str(choice)
    logging.debug(
        f'Menu execution of choice: {ch} against actions: {menu_actions}')
    if ch == '':
        main_menu(session)
    else:
        try:
            menu_actions[ch](session)
        except KeyError:
            print("Invalid selection, please try again.\n")
            # TODO: Is this okay? It works in my playground, but it seems like a hack. :)
            globals()[sys._getframe().f_back.f_code.co_name](session)


def menu(session):
    clear_screen()
    menu_actions = {
        '1': interactive_add_update_item,
        '2': interactivate_list_stock,
        '0': teardown
    }
    print("Welcome to Python Assisted Inventory (PAI)!")
    print("1) Add or update items")
    print("2) List or update stock")
    print("\n0) Quit")
    choice = get_input_int("Please choose what you would like to do?",
                           lower_bound=0,
                           upper_bound=int(max(menu_actions, key=int)))
    exec_menu(session, choice, menu_actions)


if __name__ == '__main__':
    # Initialising
    setup(basedir)
    session = db_init()

    # Read the minimum limits from the JSON and add to DB
    _quick_init(session, 'raw_data.json')

    # debug(session)
    debug_stock(session)

    # Normal operation
    logging.info('Launching the main menu for the first time')
    menu(session)
