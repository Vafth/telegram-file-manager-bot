from sqlmodel import Field, SQLModel, UniqueConstraint, Relationship
from typing import Optional
from datetime import datetime, timezone

class MediaType(SQLModel, table=True):
    __tablename__ = "media_types"

    id:                Optional[int] = Field(default = None, primary_key = True)
    short_version:     str           = Field(index   = True)
    tg_version:        str           = Field(index   = True)

    files: list["File"] = Relationship(back_populates = "media_type")

    __table_args__ = (
        UniqueConstraint('short_version', "tg_version", name="unique_media_type",),
    )

class File(SQLModel, table=True):
    __tablename__ = "files"

    id:                Optional[int] = Field(default = None, primary_key = True)
    tg_id:             str           = Field(index   = True)
    file_type:         int           = Field(index   = True, foreign_key = "media_types.id")
    backup_id:         int           = Field(index   = True)
    first_uploaded_at: datetime      = Field(default_factory=lambda: datetime.now(timezone.utc))

    media_type:   Optional[MediaType] = Relationship(back_populates = "files")

    file_folders: list["FileFolder"]  = Relationship(back_populates = "file", 
                                                    cascade_delete = True)
    
    file_users:   list["FileUser"]    = Relationship(back_populates = "file", 
                                                    cascade_delete = True)

    __table_args__ = (
        UniqueConstraint('tg_id', "file_type", "backup_id", name="unique_file",),
    )

class User(SQLModel, table=True):
    __tablename__ = "users"

    id:                  Optional[int] = Field(default = None, primary_key = True)
    chat_id:             int           = Field(unique  = True, index       = True)
    cur_folder_id:       Optional[int] = Field(default = "/",  index       = True )
    
    join_at:             datetime      = Field(default_factory=lambda: datetime.now(timezone.utc))

    folders:    list["Folder"]   = Relationship(back_populates = "user", 
                                                cascade_delete = True )
    
    file_users: list["FileUser"] = Relationship(back_populates = "user", 
                                                cascade_delete = True )

class Folder(SQLModel, table=True):
    __tablename__ = "folders"

    id:                Optional[int] = Field(default = None, primary_key = True)
    user_id:           int           = Field(index   = True, foreign_key = "users.id")
    parent_folder_id:  Optional[int] = Field(default = None, index       = True, foreign_key="folders.id")
    folder_name:       str           = Field(index   = True)
    full_path:         Optional[str] = Field(default = None, index       = True)
    created_at:        datetime      = Field(default_factory=lambda: datetime.now(timezone.utc))

    user:          Optional[User]     = Relationship(back_populates = "folders",
                                                     cascade_delete = False)

    parent_folder: Optional["Folder"] = Relationship(back_populates         = "child_folders", 
                                                     cascade_delete         = False,
                                                     sa_relationship_kwargs = {"remote_side": "Folder.id"})

    child_folders: list["Folder"]     = Relationship(back_populates = "parent_folder", 
                                                     cascade_delete = True)

    file_folders:   list["FileFolder"] = Relationship(back_populates = "folder", 
                                                     cascade_delete = False)

    __table_args__ = (
        UniqueConstraint('user_id', "parent_folder_id", "folder_name", name="unique_folder_in_folder",),
    )

class FileFolder(SQLModel, table=True):
    __tablename__ = "file_folder"

    file_id:   Optional[int] = Field(default = None, foreign_key = "files.id",    primary_key = True, ondelete="CASCADE")
    folder_id: Optional[int] = Field(default = None, foreign_key = "folders.id",  primary_key = True)
    file_name: Optional[str] = Field(default = None, index  = True)
    linked_at: datetime      = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    file:   Optional[File]     = Relationship(back_populates = "file_folders", 
                                              cascade_delete = False )

    folder: Optional[Folder] = Relationship(back_populates = "file_folders", 
                                              cascade_delete = False )

class FileUser(SQLModel, table=True):
    __tablename__ = "file_user"

    file_id:                Optional[int] = Field(default = None, foreign_key = "files.id", primary_key = True, ondelete="CASCADE")
    user_id:                Optional[int] = Field(default = None, foreign_key = "users.id", primary_key = True, ondelete="CASCADE")
    first_user_file_name: Optional[str] = Field(default = None, index  = True)
    linked_at:              datetime      = Field(default_factory=lambda: datetime.now(timezone.utc))


    file: Optional[File] = Relationship(back_populates = "file_users", 
                                        cascade_delete = False )

    user: Optional[User] = Relationship(back_populates = "file_users", 
                                        cascade_delete = False )