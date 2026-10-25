# @mcp.tool
# def delete_expense(id= None, date= None, amount= None, category= None, subcategory= None, note= None):
#     '''Remove an existing expense entry from the database'''
#     query = ("""DELETE FROM expenses WHERE 1=1""")
#     params = []

#     if date:
#         query += " AND date = ?"
#         params.append(date)

#     if amount is not None:
#         query += " AND amount = ?"
#         params.append(amount)

#     if category:
#             query += " AND category = ?"
#             params.append(category)

#     if subcategory:
#             query += " AND subcategory = ?"
#             params.append(subcategory)

#     if note:
#             query += " AND note = ?"
#             params.append(note)

#     if not params and id is None:
#          return {"status" : "error", "message" : "too few arguments. ask user to clarify expense"}

    
#     with sqlite3.connect(DB_PATH) as c:
#         if id is not None:
#             cur = c.execute("""DELETE FROM expenses where id = ?""", (id,))
#             deleted_count = cur.rowcount
#             if deleted_count > 0:
#                 return {"status": f"entry deleted entry with id = {id}"}
#             else:
#                 return {"status" : "not_found", "message" : f"Entry with id : {id} not found in database"}
        
#         cur = c.execute(query, params)
#         deleted_count = cur.rowcount

#         if deleted_count == 0:
#             return {"status" : "not_found", "message" : "No matching expense found in the database"}

#         if deleted_count == 1:
#             return {"status": "success", "message" : f"Deleted {deleted_count} expense entry from the database"}
#         else:
#             return {"status": "success", "message" : f"Deleted {deleted_count} expense entries from the database"}
