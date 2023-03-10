from fastapi import FastAPI, HTTPException, Body
from datetime import date
from pymongo import MongoClient
from pydantic import BaseModel

DATABASE_NAME = "hotel"
COLLECTION_NAME = "reservation"
MONGO_DB_URL = "mongodb://localhost"
MONGO_DB_PORT = 8000


class Reservation(BaseModel):
    name : str
    start_date: date
    end_date: date
    room_id: int


client = MongoClient(f"{MONGO_DB_URL}:{MONGO_DB_PORT}")

db = client[DATABASE_NAME]

collection = db[COLLECTION_NAME]

app = FastAPI()


def room_avaliable(room_id: int, start_date: str, end_date: str):
    query={"room_id": room_id,
           "$or": 
                [{"$and": [{"start_date": {"$lte": start_date}}, {"end_date": {"$gte": start_date}}]},
                 {"$and": [{"start_date": {"$lte": end_date}}, {"end_date": {"$gte": end_date}}]},
                 {"$and": [{"start_date": {"$gte": start_date}}, {"end_date": {"$lte": end_date}}]}]
            }
    
    result = collection.find(query, {"_id": 0})
    list_cursor = list(result)

    return not len(list_cursor) > 0


@app.get("/reservation/by-name/{name}")
def get_reservation_by_name(name:str):
    return list(collection.find({"name":name}))

@app.get("/reservation/by-room/{room_id}")
def get_reservation_by_room(room_id: int):
    return list(collection.find({"room_id":room_id}))

@app.post("/reservation")
def reserve(reservation : Reservation):
    if (room_avaliable(reservation.room_id, reservation.start_date, reservation.end_date)):
        collection.insert_one({"room_id":reservation.room_id,
                              "name":reservation.name, 
                              "start_date":str(reservation.start_date),
                              "end_date":str(reservation.end_date)})
    else:
        raise HTTPException(404)

@app.put("/reservation/update")
def update_reservation(reservation: Reservation, new_start_date: date = Body(), new_end_date: date = Body()):
    if(bool(collection.find({"room_id":reservation.room_id,
                              "name":reservation.name, 
                              "start_date":str(reservation.start_date),
                              "end_date":str(reservation.end_date)}))):
        if(room_avaliable(reservation.room_id, new_start_date,new_end_date)):
            collection.update_one({"room_id":reservation.room_id,
                                    "name":reservation.name, 
                                    "start_date":str(reservation.start_date),
                                    "end_date":str(reservation.end_date)},
                                    update= 
                                    {"start_date":str(new_start_date),
                                    "end_date":str(new_end_date)})
        else:
            raise HTTPException(404)
    else:
        raise HTTPException(404)

@app.delete("/reservation/delete")
def cancel_reservation(reservation: Reservation):
     if(bool(collection.find({"room_id":reservation.room_id,
                              "name":reservation.name, 
                              "start_date":str(reservation.start_date),
                              "end_date":str(reservation.end_date)}))):
         collection.delete_one({"room_id":reservation.room_id,
                              "name":reservation.name, 
                              "start_date":str(reservation.start_date),
                              "end_date":str(reservation.end_date)})