from fastapi import APIRouter, Depends

from app.deps import get_current_user
from app.schemas.book import *
from app.schemas.common import *
from app.utils.book import Book
from app.utils.decorators import require_permission

router = APIRouter()


@router.get("/list")
def book_list():
    books = Book().get_list()
    if not books:
        return ResponseNormal(msg="暂无数据")
    return ListBooksResponse(
        msg="获取图书列表成功",
        data=books
    )


@router.post("/add")
@require_permission(level=1)
def book_add(req: AddBooksRequest, user=Depends(get_current_user)):
    book = Book().add_book(req.data)
    if book:
        return ResponseNormal(msg="添加图书成功")
    return ResponseNormal(msg="添加图书失败", code=1)


@router.post("/update")
@require_permission(level=1)
def book_update(req: UpdateBookRequest, user=Depends(get_current_user)):
    book = Book(req.bookId, req.title, req.author, req.description, req.pic, req.type, req.price, req.count).update_book()
    if book:
        return ResponseNormal(msg="更新图书成功")
    return ResponseNormal(msg="更新图书失败", code=1)


@router.get("/del")
@require_permission(level=1)
def book_del(bookId: int, user=Depends(get_current_user)):
    if Book(bookId).del_book():
        return ResponseNormal(msg="删除图书成功")
    return ResponseNormal(msg="删除图书失败", code=1)


@router.post("/borrow")
def book_borrow(req: BorrowBookRequest, user=Depends(get_current_user)):
    if Book(req.bookId).borrow_book(req.borrowLong, user.username):
        return ResponseNormal(msg="借书成功")
    return ResponseNormal(msg="借书失败", code=1)


@router.post("/return")
def book_return(req: ReturnBookRequest, user=Depends(get_current_user)):
    if Book(req.bookId).return_book(user.username):
        return ResponseNormal(msg="还书成功")
    return ResponseNormal(msg="还书失败", code=1)


@router.get("/borrowList")
def book_borrow_list(user=Depends(get_current_user)):
    records = Book().get_circulate_list(user.username, user.permission)
    if not records:
        return ResponseNormal(msg="暂无借阅记录")
    return ListBorrowsResponse(
        msg="获取借阅列表成功",
        data=records
    )
