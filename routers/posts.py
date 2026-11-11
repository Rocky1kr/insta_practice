# 설치한 모듈들
from fastapi import Request, Form, HTTPException, APIRouter
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import selectinload

# 우리가 만든파일
from models import Post, Comment, Like
from deps import templates, SessionDep, CurrentUserDep, PostDep, safe_next

router = APIRouter()


def get_liked_ids(db, user) -> set[int]:
  # 로그인한 유저가 좋아요 누른 게시물 id 목록
  if user is None:
    return set()
  return set(db.scalars(select(Like.post_id).where(Like.user_id == user.id)).all())


@router.get('/posts')
def post_list(request: Request, db: SessionDep, user: CurrentUserDep):
  posts = db.scalars(
    select(Post)
    .options(selectinload(Post.comments), selectinload(Post.user), selectinload(Post.likes))  # N+1 쿼리 방지
    .order_by(Post.created_at.desc())
  ).all()
  return templates.TemplateResponse(
    request=request,
    name='list.html',
    context={'posts': posts, 'user': user, 'liked_ids': get_liked_ids(db, user)}
  )


@router.get('/posts/new')
def post_new(request: Request, user: CurrentUserDep):
  # 로그인 하지 않은사람이라면
  if user is None:
    return RedirectResponse('/login', status_code=303)

  return templates.TemplateResponse(
    request=request,
    name='new.html',
    context={'user': user}
  )


@router.post('/posts/create')
def post_create(db: SessionDep, user: CurrentUserDep, content: str = Form()):
  if user is None:
    return RedirectResponse('/login', status_code=303)

  post = Post(content=content, user=user)
  db.add(post)
  db.commit()

  return RedirectResponse('/posts', status_code=303)


@router.get('/posts/{post_id}')
def post_detail(request: Request, post: PostDep, db: SessionDep, user: CurrentUserDep):
  return templates.TemplateResponse(
    request=request,
    name='detail.html',
    context={'post': post, 'user': user, 'liked_ids': get_liked_ids(db, user)}
  )


@router.get('/posts/{post_id}/edit')
def post_edit(request: Request, post: PostDep, user: CurrentUserDep):
  if user is None:
    return RedirectResponse('/login', status_code=303)

  # 게시물 작성자와 로그인한 사람 비교
  if post.user_id != user.id:
    raise HTTPException(status_code=403, detail='내 글만 수정할 수 있습니다.')

  return templates.TemplateResponse(
    request=request,
    name='edit.html',
    context={'post': post, 'user': user}
  )


@router.post('/posts/{post_id}/update')
def post_update(post: PostDep, db: SessionDep, user: CurrentUserDep, content: str = Form()):
  if user is None:
    return RedirectResponse('/login', status_code=303)

  # 게시물 작성자와 로그인한 사람 비교
  if post.user_id != user.id:
    raise HTTPException(status_code=403, detail='내 글만 수정할 수 있습니다.')

  post.content = content
  db.commit()

  return RedirectResponse(f'/posts/{post.id}', status_code=303)


@router.post('/posts/{post_id}/delete')
def post_delete(post: PostDep, db: SessionDep, user: CurrentUserDep):
  if user is None:
    return RedirectResponse('/login', status_code=303)

  # 게시물 작성자와 로그인한 사람 비교
  if post.user_id != user.id:
    raise HTTPException(status_code=403, detail='내 글만 삭제할 수 있습니다.')

  db.delete(post)
  db.commit()
  return RedirectResponse('/posts', status_code=303)


@router.post('/posts/{post_id}/comments/create')
def comment_create(post: PostDep, db: SessionDep, user: CurrentUserDep, content: str = Form()):
  if user is None:
    return RedirectResponse('/login', status_code=303)

  comment = Comment(content=content, post=post, user=user)
  db.add(comment)
  db.commit()

  return RedirectResponse(f'/posts/{post.id}', status_code=303)


@router.post('/posts/{post_id}/comments/{comment_id}/delete')
def comment_delete(post_id: int, comment_id: int, db: SessionDep, user: CurrentUserDep):
  # 로그인 안한사람
  if user is None:
    return RedirectResponse('/login', status_code=303)

  # 이미 지워졌거나 다른 게시물의 댓글이면 404
  comment = db.get(Comment, comment_id)
  if comment is None or comment.post_id != post_id:
    raise HTTPException(status_code=404, detail='해당 댓글이 없습니다.')

  # 내가 쓴 댓글인지
  if comment.user_id != user.id:
    raise HTTPException(status_code=403, detail='내 댓글만 삭제할 수 있습니다.')

  db.delete(comment)
  db.commit()

  return RedirectResponse(f'/posts/{post_id}', status_code=303)


@router.post('/posts/{post_id}/likes')
def post_like(post: PostDep, db: SessionDep, user: CurrentUserDep, next: str | None = Form(None)):
  if user is None:
    return RedirectResponse('/login', status_code=303)

  # like가 이미 있는지?
  like = db.get(Like, (user.id, post.id))

  if like:
    # 좋아요가 이미 눌린경우 => 취소
    db.delete(like)
  else:
    # 아직 좋아요 안누른경우
    db.add(Like(user_id=user.id, post_id=post.id))

  db.commit()

  # 누른 화면(피드/상세)으로 돌아가기
  return RedirectResponse(safe_next(next), status_code=303)
