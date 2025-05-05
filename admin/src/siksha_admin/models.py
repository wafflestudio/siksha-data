import re

from sqlalchemy import (
    DATE,
    TIMESTAMP,
    Boolean,
    Double,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    declared_attr,
    mapped_column,
    query_expression,
    relationship,
)
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    @declared_attr.directive
    def __tablename__(cls) -> str:  # noqa: N805
        return re.sub("(?<!^)(?=[A-Z])", "_", cls.__name__).lower()

    metadata = MetaData(
        naming_convention={
            "ix": "%(table_name)s_%(column_0_N_name)s_index",
        }
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[str] = mapped_column(
        TIMESTAMP(timezone=False), server_default=func.now(), nullable=False, comment="생성 시간"
    )
    updated_at: Mapped[str] = mapped_column(
        TIMESTAMP(timezone=False),
        server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
        nullable=False,
        comment="변경 시간",
    )


class Version(Base):
    version: Mapped[str] = mapped_column(String(20), nullable=False, comment="버전")
    minimum_version: Mapped[str] = mapped_column(String(20), nullable=False, comment="최소 버전")
    client_type: Mapped[str] = mapped_column(
        String(10), nullable=False, comment="클라이언트 타입(AND, IOS, WEB)"
    )


class EtcMixin:
    etc: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="기타 정보(json 형태로 유연하게 저장)"
    )


class User(EtcMixin, Base):
    type: Mapped[str] = mapped_column(
        String(10), nullable=False, comment="사용자 타입(GOOGLE, APPLE, ...)"
    )
    identity: Mapped[str] = mapped_column(String(200), nullable=False, comment="사용자 식별자")
    nickname: Mapped[str] = mapped_column(String(30), nullable=False, comment="사용자 닉네임")
    profile_url: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="사용자 프로필 url"
    )
    transfer_sub: Mapped[str | None] = mapped_column(
        String(200), nullable=True, comment="애플 계정 이전을 위한 transfer sub"
    )
    __table_args__ = (
        UniqueConstraint("type", "identity"),
        UniqueConstraint("nickname"),
    )


class Restaurant(EtcMixin, Base):
    code: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="식당 식별자(크롤러에서 사용)"
    )
    name_kr: Mapped[str | None] = mapped_column(String(200), nullable=True, comment="식당명(한글)")
    name_en: Mapped[str | None] = mapped_column(String(200), nullable=True, comment="식당명(영어)")
    addr: Mapped[str | None] = mapped_column(String(200), nullable=True, comment="주소")
    lat: Mapped[float | None] = mapped_column(Double, nullable=True, comment="위도")
    lng: Mapped[float | None] = mapped_column(Double, nullable=True, comment="경도")
    __table_args__ = (UniqueConstraint("code"),)


class Menu(EtcMixin, Base):
    restaurant_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("restaurant.id", ondelete="CASCADE"),
        nullable=False,
        comment="메뉴가 제공되는 식당의 id",
    )
    restaurant: Mapped["Restaurant"] = relationship("Restaurant", backref="menus")
    code: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="메뉴 식별자(크롤러에서 사용)"
    )
    date: Mapped[str] = mapped_column(
        DATE, index=True, nullable=False, comment="메뉴가 제공되는 날짜"
    )
    type: Mapped[str] = mapped_column(
        String(10), nullable=False, comment="메뉴 제공 타입(BR,LU,DN,AL,...)"
    )
    name_kr: Mapped[str | None] = mapped_column(String(200), nullable=True, comment="메뉴명(한글)")
    name_en: Mapped[str | None] = mapped_column(String(200), nullable=True, comment="메뉴명(영어)")
    price: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="가격")
    __table_args__ = (
        UniqueConstraint("restaurant_id", "code", "date", "type"),
        Index(None, "code", "restaurant_id"),
    )


class Review(EtcMixin, Base):
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("user.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        comment="리뷰를 작성한 사용자의 id",
    )
    menu_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("menu.id", ondelete="CASCADE"),
        nullable=False,
        comment="리뷰의 대상 메뉴 id",
    )
    score: Mapped[int] = mapped_column(Integer, nullable=False, comment="메뉴에 대한 평점")
    comment: Mapped[str | None] = mapped_column(Text, nullable=True, comment="메뉴에 대한 리뷰")
    user: Mapped["User"] = relationship("User", backref="reviews")
    menu: Mapped["Menu"] = relationship("Menu", backref="reviews")
    __table_args__ = (UniqueConstraint("menu_id", "user_id"),)


class MenuLike(Base):
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("user.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        comment="좋아요를 남긴 유저",
    )
    menu_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("menu.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        comment="좋아요를 남긴 메뉴",
    )
    is_liked: Mapped[bool | None] = mapped_column(Boolean, comment="좋아요 여부")
    user: Mapped["User"] = relationship("User", backref="menu_likes")
    menu: Mapped["Menu"] = relationship("Menu", backref="menu_likes")
    __table_args__ = (UniqueConstraint("menu_id", "user_id"),)


class Board(Base):
    name: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="게시판 이름", unique=True
    )
    description: Mapped[str] = mapped_column(Text, nullable=False, comment="게시판 설명")
    type: Mapped[int] = mapped_column(
        Integer, server_default="1", nullable=False, comment="게시판 타입(학식,외식)"
    )


class Post(EtcMixin, Base):
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("user.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        comment="게시글을 작성한 유저",
    )
    board_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("board.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        comment="게시글이 작성된 게시판",
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False, comment="게시글 제목")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="게시글 내용")
    available: Mapped[bool | None] = mapped_column(Boolean, default=True, comment="표시 여부")
    anonymous: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="익명 여부"
    )

    user: Mapped["User"] = relationship("User", backref="posts")
    board: Mapped["Board"] = relationship("Board", backref="posts")
    # 양방향 관계 설정
    post_likes: Mapped[list["PostLike"]] = relationship("PostLike", back_populates="post")

    like_cnt: Mapped[int] = query_expression()
    comment_cnt: Mapped[int] = query_expression()

    is_liked: Mapped[bool] = query_expression()
    nickname: Mapped[str] = query_expression()
    is_mine: Mapped[bool] = query_expression()
    profile_url: Mapped[str] = query_expression()


class PostLike(Base):
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("user.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        comment="좋아요를 남긴 유저",
    )
    post_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("post.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        comment="좋아요를 남긴 게시글",
    )
    is_liked: Mapped[bool | None] = mapped_column(Boolean, comment="좋아요 여부")
    user: Mapped["User"] = relationship("User", backref="post_likes")
    post: Mapped["Post"] = relationship("Post", back_populates="post_likes")
    __table_args__ = (UniqueConstraint("post_id", "user_id"),)


class Comment(Base):
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("user.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        comment="댓글을 작성한 유저",
    )
    post_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("post.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        comment="댓글이 작성된 게시글",
    )
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="댓글 내용")
    available: Mapped[bool | None] = mapped_column(Boolean, default=True, comment="표시 여부")
    anonymous: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="익명 여부"
    )

    user: Mapped["User"] = relationship("User", backref="comments")
    post: Mapped["Post"] = relationship("Post", backref="comments")

    like_cnt: Mapped[int] = query_expression()
    is_liked: Mapped[bool] = query_expression()
    nickname: Mapped[str] = query_expression()
    is_mine: Mapped[bool] = query_expression()
    profile_url: Mapped[str] = query_expression()


class CommentLike(Base):
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("user.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        comment="좋아요를 남긴 유저",
    )
    comment_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("comment.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        comment="좋아요를 남긴 댓글",
    )
    is_liked: Mapped[bool | None] = mapped_column(Boolean, comment="좋아요 여부")
    user: Mapped["User"] = relationship("User", backref="comment_likes")
    comment: Mapped["Comment"] = relationship("Comment", backref="comment_likes")
    __table_args__ = (UniqueConstraint("comment_id", "user_id"),)


class ReportMixin:
    @declared_attr
    def reporting_uid(cls) -> Mapped[int | None]:  # noqa: N805
        return mapped_column(
            Integer,
            ForeignKey("user.id", ondelete="CASCADE"),
            index=True,
            nullable=True,
            comment="신고자 ID",
        )

    @declared_attr
    def reported_uid(cls) -> Mapped[int]:  # noqa: N805
        return mapped_column(
            Integer,
            ForeignKey("user.id", ondelete="CASCADE"),
            index=True,
            nullable=False,
            comment="신고 당한 유저 ID",
        )

    reason: Mapped[str] = mapped_column(String(200), nullable=False, comment="신고 사유")


class PostReport(ReportMixin, Base):
    post_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("post.id", ondelete="CASCADE", name="fk_post_report_post_id"),
        index=True,
        nullable=False,
        comment="게시글 ID",
    )
    post: Mapped["Post"] = relationship("Post", backref="reports")

    __table_args__ = (UniqueConstraint("post_id", "reporting_uid"),)


class CommentReport(ReportMixin, Base):
    comment_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("comment.id", ondelete="CASCADE", name="fk_comment_report_comment_id"),
        index=True,
        nullable=False,
        comment="댓글 ID",
    )
    comment: Mapped["Comment"] = relationship("Comment", backref="reports")

    __table_args__ = (UniqueConstraint("comment_id", "reporting_uid"),)


class Image(Base):
    key: Mapped[str] = mapped_column(String(60), nullable=False, comment="이미지 key")
    category: Mapped[str] = mapped_column(
        String(10), nullable=False, comment="이미지 카테고리(POST, PROFILE, REVIEW, ...)"
    )
    user_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="이미지를 올린 유저"
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, comment="삭제 여부")

    __table_args__ = (UniqueConstraint("key"),)


class AdminUser(Base):
    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, comment="관리자 아이디"
    )
    password_hash: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="암호화된 비밀번호"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="계정 활성화 상태"
    )
    role: Mapped[str] = mapped_column(
        String(20), default="admin", nullable=False, comment="관리자 권한"
    )
    last_login: Mapped[str | None] = mapped_column(
        TIMESTAMP(timezone=False), nullable=True, comment="마지막 로그인 시간"
    )


class RestaurantRequest(Base):
    owner_name: Mapped[str] = mapped_column(String(100), nullable=False, comment="신청자 이름")
    phone: Mapped[str] = mapped_column(String(30), nullable=False, comment="연락처")
    email: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="이메일")
    restaurant_name: Mapped[str] = mapped_column(String(200), nullable=False, comment="식당 이름")
    addr: Mapped[str | None] = mapped_column(String(200), nullable=True, comment="식당 주소")
    business_number: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="사업자 등록 번호"
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        server_default="pending",
        comment="승인 상태 (pending, approved, rejected)",
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True, comment="관리자 메모")
    processed_at: Mapped[str | None] = mapped_column(
        TIMESTAMP(timezone=False), nullable=True, comment="처리 시간"
    )
    __table_args__ = (
        UniqueConstraint("phone", "restaurant_name"),
        UniqueConstraint("business_number"),
    )
