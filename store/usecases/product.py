from datetime import datetime
from typing import List
from uuid import UUID
from motor.core import AgnosticClient
import pymongo
from pymongo.database import Database
from store.db.mongo import db_client
from store.models.product import ProductModel
from store.schemas.product import ProductIn, ProductOut, ProductUpdate, ProductUpdateOut
from store.core.exceptions import NotFoundException, BaseException


class ProductUsecase:
    def __init__(self) -> None:
        self.client: AgnosticClient = db_client.get()
        self.database: Database = self.client.get_database()
        self.collection = self.database.get_collection("products")

    async def create(self, body: ProductIn) -> ProductOut:
        product_model = ProductModel(**body.model_dump())
        if product_model.quantity < 0:
            raise BaseException(message="Quantidade não pode ser negativa")
        self.collection.insert_one(product_model.model_dump())

        return ProductOut(**product_model.model_dump())

    async def get(self, id: UUID) -> ProductOut:
        result = await self.collection.find_one({"id": id})

        if not result:
            raise NotFoundException(
                message=f"Product not found with filter: {id}")

        return ProductOut(**result)

    async def query(self, apply_filter: bool) -> List[ProductOut]:
        filter = {}
        if apply_filter:
            filter = {"price": {"$lt": 8000, "$gt": 5000}}
        return [ProductOut(**item) async for item in self.collection.find(
            filter=filter
        )]

    async def update(self, id: UUID, body: ProductUpdate) -> ProductUpdateOut:
        if not body.updated_at:
            body.updated_at = datetime.now()
        result = await self.collection.find_one_and_update(
            filter={"id": id},
            update={"$set": body.model_dump(exclude_none=True)},
            return_document=pymongo.ReturnDocument.AFTER,
        )

        if result is None:
            raise NotFoundException(
                message=f"Product not found with filter: {id}")

        return ProductUpdateOut(**result)

    async def delete(self, id: UUID) -> bool:
        product = await self.collection.find_one({"id": id})
        if not product:
            raise NotFoundException(
                message=f"Product not found with filter: {id}")

        result = await self.collection.delete_one({"id": id})

        return True if result.deleted_count > 0 else False


product_usecase = ProductUsecase()
