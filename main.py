import json
import logging
import functools
from abc import ABC, abstractmethod
from typing import List, Iterator, Generator
from pydantic import BaseModel


class BookModel(BaseModel):
    title: str
    author: str
    year: int


class JournalModel(BookModel):
    volume: str


#abs class for library items
class LibraryItem(ABC):
    @abstractmethod
    def get_info(self):
        ...


#book, journal classes
class Book(LibraryItem):

    def __init__(self, model: BookModel):
        self._title: str = model.title
        self._author: str = model.author
        self._year: int = model.year

    @property
    def author(self):
        return self._author

    def get_info(self):
        return f"Book: {self._title} by {self._author} ({self._year})"

    def __eq__(self, other: object):
        if not isinstance(other, Book):
            return False
        return (
            self._title == other._title and
            self._author == other._author and
            self._year == other._year
        )

    def __str__(self):
        return self.get_info()


class Journal(Book):

    def __init__(self, model: JournalModel):
        super().__init__(model)
        self._volume: str = model.volume

    def get_info(self):
        return f"Journal: {self._title} by {self._author} ({self._year}), volume: {self._volume}"  

    def __eq__(self, other: object):
        if not isinstance(other, Journal):
            return False
        return super().__eq__(other) and self._volume == other._volume

    def __str__(self):
        return self.get_info()


#logging cfg
logging.basicConfig(
    filename='library.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s'
)

#decorators
def log_add(func):
    @functools.wraps(func)
    def wrapper(self, item: LibraryItem, *args, **kwargs):
        result = func(self, item, *args, **kwargs)
        logging.info(f"Added to library: {item.get_info()}")
        return result
    return wrapper


def log_remove(func):
    @functools.wraps(func)
    def wrapper(self, item: LibraryItem, *args, **kwargs):
        result = func(self, item, *args, **kwargs)
        logging.info(f"Removed from library: {item.get_info()}")
        return result
    return wrapper


def ensure_exists(func):
    @functools.wraps(func)
    def wrapper(self, item: LibraryItem, *args, **kwargs):
        if item not in self._items:
            raise ValueError(f"Cannot remove—item not found: {item.get_info()}")
        return func(self, item, *args, **kwargs)
    return wrapper


#library class
class Library:

    def __init__(self):
        self._items: List[LibraryItem] = []

    def __iter__(self) -> Iterator[LibraryItem]:
        return iter(self._items)

    def books_by_author(self, author: str) -> Generator[LibraryItem, None, None]:
        for it in self._items:
            if getattr(it, 'author', None) == author:
                yield it

    @log_add
    def add_book(self, item: LibraryItem):
        self._items.append(item)

    @log_remove
    @ensure_exists
    def remove_book(self, item: LibraryItem):
        self._items.remove(item)


#context manager
class FileManager:
    def __init__(self, filename: str):
        self.filename = filename

    def __enter__(self) -> 'FileManager':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        return False

    def save(self, items: List[LibraryItem]) -> None:

        data = []
        for it in items:
            entry = {
                'type': it.__class__.__name__,
                'title': it._title,
                'author': it._author,
                'year': it._year
            }
            if isinstance(it, Journal):
                entry['volume'] = it._volume
            data.append(entry)
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def load(self) -> List[LibraryItem]:

        with open(self.filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        restored: List[LibraryItem] = []

        for entry in data:
            if entry['type'] == 'Book':
                model = BookModel(**{k: entry[k] for k in ('title', 'author', 'year')})
                restored.append(Book(model))
            elif entry['type'] == 'Journal':
                model = JournalModel(**{k: entry[k] for k in ('title', 'author', 'year', 'volume')})
                restored.append(Journal(model))

        return restored


#instances
if __name__ == '__main__':

    lib = Library()

    b1 = BookModel(title='Cyberpunk', author='CD Project RED', year=2077)
    j1 = JournalModel(title='something', author='Pepsi', year=1999, volume='Learn python xd')
    book = Book(b1)
    journal = Journal(j1)

    lib.add_book(book)
    lib.add_book(journal)

    print("All items in library:")
    for item in lib:
        print(" ", item)

    print("\nItems by CD Project RED:") #whatever
    for item in lib.books_by_author('CD Project RED'):
        print(" ", item)

    with FileManager('books.json') as fileman:
        fileman.save(list(lib))

    lib.remove_book(book)

    print("\nAfter removal:")
    for item in lib:
        print(" ", item)

    with FileManager('books.json') as fileman:
        loaded = fileman.load()
    for item in loaded:
        lib.add_book(item)

    print("\nAfter loading from file:")
    for item in lib:
        print(" ", item)
