from sqlalchemy.orm import Mapped, mapped_column

from src.model.meta import Base


class FileRecord(Base):
    __tablename__ = 'file_records'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(index=True)
    file_name: Mapped[str] = mapped_column(index=True)
    file_path: Mapped[str] = mapped_column(index=True)
    file_exention: Mapped[str] = mapped_column(index=True)
