import time

from pydantic import BaseModel


class BookDataBase(BaseModel):
    id: int
    book_id: int
    title: str
    author: str
    description: str
    pic: str
    type: str
    price: int
    count: int
    borrow_count: int


class BorrowInfo(BaseModel):
    id: int
    bookId: int
    username: str
    borrowTime: int
    borrowLong: int
    returnTime: int
    isReturn: bool
    isTimeOut: bool


class AddBookRequest(BaseModel):
    title: str
    author: str
    description: str
    pic: str
    type: str
    price: int
    count: int


class AddBooksRequest(BaseModel):
    data: list[AddBookRequest]


class UpdateBookRequest(BaseModel):
    bookId: int
    title: str
    author: str
    description: str
    pic: str
    type: str
    price: int
    count: int


class BorrowBookRequest(BaseModel):
    bookId: int
    borrowLong: int


class ReturnBookRequest(BaseModel):
    bookId: int


class ListBooksResponse(BaseModel):
    msg: str
    data: list[BookDataBase]
    code: int = 0
    time: int = round(time.time() * 1000)


class ListBorrowsResponse(BaseModel):
    msg: str
    data: list[BorrowInfo]
    code: int = 0
    time: int = round(time.time() * 1000)
