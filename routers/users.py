from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import select, func
from deps import templates, SessionDep, CurrentUserDep
from models import User, Post, Follow

router = APIRouter()


def get_user_or_404(db, username: str) -> User:
  owner = db.scalar(select(User).where(User.username == username))
  if owner is None:
    raise HTTPException(status_code=404, detail='해당 사용자가 없습니다.')
  return owner


@router.get('/users/{username}')
def user_profile(request: Request, username: str, db: SessionDep, user: CurrentUserDep):
  # 보려고 하는 프로필 유저
  owner = get_user_or_404(db, username)

  # 프로필 유저가 작성한 모든 게시물
  posts = db.scalars(
    select(Post).where(Post.user_id == owner.id).order_by(Post.created_at.desc())
  ).all()

  # 팔로워 = 이 프로필을 팔로우하는 사람 수 (화살표를 받는 쪽이 owner)
  follower_count = db.scalar(select(func.count()).where(Follow.following_id == owner.id))
  # 팔로잉 = 이 프로필이 팔로우하는 사람 수 (화살표를 보내는 쪽이 owner)
  following_count = db.scalar(select(func.count()).where(Follow.follower_id == owner.id))

  # 로그인한 내가 이 프로필을 팔로우 중인지
  is_following = bool(user and db.get(Follow, (user.id, owner.id)))

  return templates.TemplateResponse(
    request=request,
    name='profile.html',
    context={
      'owner': owner,
      'posts': posts,
      'user': user,
      'follower_count': follower_count,
      'following_count': following_count,
      'is_following': is_following,
    }
  )


@router.post('/users/{username}/follows')
def user_follow(username: str, db: SessionDep, user: CurrentUserDep):
  # 비로그인 유저 로그인페이지로
  if user is None:
    return RedirectResponse('/login', status_code=303)

  owner = get_user_or_404(db, username)

  # 내가 나를 팔로우할 수 없음
  if owner.id == user.id:
    raise HTTPException(status_code=400, detail='자기 자신은 팔로우할 수 없습니다.')

  # 팔로우 했는지 조회
  follow = db.get(Follow, (user.id, owner.id))

  if follow:
    # 팔로우 했다면 => 언팔로우
    db.delete(follow)
  else:
    # 팔로우 안했으면
    db.add(Follow(follower_id=user.id, following_id=owner.id))

  db.commit()

  return RedirectResponse(f'/users/{username}', status_code=303)
