from sqlalchemy import Column, Integer, String, Date, Boolean
from sqlalchemy import ForeignKey
from sqlalchemy import Sequence
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import ClauseElement


Base = declarative_base()


class Item(Base):
    __tablename__ = 'item'

    id = Column(Integer, Sequence('item_id_seq'), primary_key=True)
    name = Column(String(50))
    name_dk = Column(String(50))
    group_id = Column(Integer(), ForeignKey('itemgroup.id'))
    type_id = Column(Integer(), ForeignKey('containertype.id'))
    standard_duration = Column(Integer())
    min_limit = Column(Integer())

    # Relationships
    itemgroup = relationship("ItemGroup", back_populates="item")
    containertype = relationship("ContainerType", back_populates="item")
    barcode = relationship("Barcode", order_by="Barcode.id",
                           back_populates="item")
    storage = relationship("Storage", back_populates="item")

    def get_name(self):
        '''Returns "Item Name" either as "Name" or "Name (Container)"'''
        name_type = self.name
        if self.containertype:
            name_type = f'{self.name} ({self.containertype.name})'
        return name_type

    def __repr__(self):
        return f"<Item(name='{self.get_name()}', id='{self.id}', mininimum='{self.min_limit}', group_id='{self.group_id}', std_duration='{self.standard_duration}')>"

    def set_min(self, minimum=None):
        '''Specify the minimum limit for the item, defaults to no limit'''
        self.min_limit = minimum

    def set_std_dur(self, duration=None):
        '''Specify the standard duration (in days) for the item, defaults to none'''
        self.standard_duration = duration

    def get_std_dur(self):
        '''Return the standard duration (in days) for the item, defaults to none'''
        return self.standard_duration

    def get_info(self, prefix=None, short=False):
        '''Returns pretty-printed prefixable version of the Item with min-limit'''
        name = self.get_name()
        if prefix:
            name = prefix + name
        info = f"{name} (id: {self.id})"
        if not short:
            info = info + f" - Min Limit: {self.min_limit}"
        return info


class Storage(Base):
    __tablename__ = 'storage'

    id = Column(Integer, Sequence('storage_id_seq'), primary_key=True)
    item_id = Column(Integer(), ForeignKey('item.id'))
    storage_date = Column(Date())
    expiration_date = Column(Date())
    portions = Column(Integer())
    location_id = Column(Integer(), ForeignKey('location.id'))

    # Relationships
    item = relationship("Item", order_by=Item.id, back_populates="storage")
    location = relationship("Location", back_populates="storage")

    def get_location(self):
        return f"{self.location.name} (id: {self.location_id})"

    def get_item(self):
        return f"{self.item.name} (id: {self.item_id})"

    def __repr__(self):
        return f"<Storage(id='{self.id}', item='{self.get_item()}', portions='{self.portions}', storage_location='{self.get_location()}', storage_date='{self.storage_date}', expiration_date='{self.expiration_date}')>"

    def get_store_info(self):
        store_info = f"{self.storage_date}"
        if self.expiration_date is not None:
            store_info = store_info + f" (Expire: {self.expiration_date})"
        return store_info

    def get_row(self, prefix=None):
        '''Returns pretty-printed prefiable version of the storage row with storage and expiration dates'''
        row_info = f"Item: {self.get_item()}, #Portions: {self.portions}, stored on: {self.get_store_info()}"
        if prefix:
            row_info = prefix + row_info
        return row_info


class Location(Base):
    __tablename__ = 'location'

    id = Column(Integer, Sequence('location_id_seq'), primary_key=True)
    name = Column(String(50))

    # Relationships
    storage = relationship("Storage", order_by=Storage.id,
                           back_populates="location")

    def __repr__(self):
        return f"<Location(name='{self.name}', id='{self.id}')>"


class Barcode(Base):
    __tablename__ = 'barcode'

    id = Column(Integer, Sequence('barcode_id_seq'), primary_key=True)
    barcode = Column(String(50), unique=True)
    item_id = Column(Integer(), ForeignKey('item.id'))

    # Relationships
    item = relationship("Item", back_populates="barcode")

    def __repr__(self):
        return f"<Barcode(barcode='{self.barcode}', id='{self.id}', item_id='{self.item_id}')>"


class ItemGroup(Base):
    __tablename__ = 'itemgroup'

    id = Column(Integer, Sequence('itemgroup_id_seq'), primary_key=True)
    name = Column(String(50), unique=True)

    # Relationships
    item = relationship("Item", order_by=Item.id, back_populates="itemgroup")

    def __repr__(self):
        return f"<ItemGroup(name='{self.name}', id='{self.id}')>"


class ContainerType(Base):
    __tablename__ = 'containertype'

    id = Column(Integer, Sequence('containertype_id_seq'), primary_key=True)
    name = Column(String(50), unique=True)

    # Relationships
    item = relationship("Item", order_by=Item.id,
                        back_populates="containertype")

    def __repr__(self):
        return f"<ContainerType(name='{self.name}', id='{self.id}')>"


def _create(session, model, defaults=None, id=None, **kwargs):
    '''
    Get_or_create method - defaults will overwrite **kwargs.

    :returns a tuple (instance, created):
        instance of the data
        boolean of whether it was created
    '''
    if id:
        instance = session.query(model).filter(model.id == id).first()
    else:
        instance = session.query(model).filter_by(**kwargs).first()

    if instance:
        return instance, False
    else:
        params = dict((k, v) for k, v in kwargs.items()
                      if not isinstance(v, ClauseElement))
        params.update(defaults or {})
        instance = model(**params)
        session.add(instance)
        return instance, True
