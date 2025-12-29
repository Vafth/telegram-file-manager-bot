from sqlmodel import delete
from ..models import Folder, FileFolder


from sqlalchemy.ext.asyncio import AsyncSession

async def delete_file_folder_link(
            session:   AsyncSession, 
            file_id:   int, 
            folder_id: int
        ) -> bool:

    delete_link_result = await session.execute(
        delete(FileFolder)
        .where(
            FileFolder.file_id == file_id,
            FileFolder.folder_id == folder_id
        )
        .returning(FileFolder)
    )
    result = delete_link_result.scalars().one_or_none()
    
    return result is not None 

async def delete_folder_by_id(session: AsyncSession, folder_id: int):    
    await session.execute(
        delete(Folder)
        .where(Folder.id == folder_id)
    )
