from suql import suql_execute

# Find a peaceful event
suql = "SELECT * FROM events WHERE answer(description, 'is this a dance related event?') = 'Yes' LIMIT 3;"

# Find an event that combines relaxation with physical activity
# suql =  "SELECT * FROM events WHERE answer(description, 'Does this event combine relaxation with physical activity?') = 'Yes' LIMIT 3;"

# Find an upcoming game related event
# suql = "SELECT * FROM events WHERE start_time >= CURRENT_TIMESTAMP AND start_time <= CURRENT_TIMESTAMP + INTERVAL '7 days' AND answer(description, 'is this a game related event') = 'Yes' LIMIT 3;"

table_w_ids = {"events": "_id"}

fts_fields = [("events", "description")]

database = "vrchat_events"

result = suql_execute(
        suql=suql,
        table_w_ids=table_w_ids, 
        database=database, 
        fts_fields=fts_fields,
        llm_model_name="gpt-4o",
        disable_try_catch=True
        )

print(result)

# from suql import suql_execute

# Common parameters
# table_w_ids = {"events": "_id"}
# fts_fields = [("events", "description")]
# database = "vr_event_hub"
# llm_model_name = "gpt-4o"
# disable_try_catch = True

# # Define test cases
# test_cases = [
#     {
#         "query": "SELECT * FROM events WHERE answer(description, 'is this a peaceful event?') = 'Yes' LIMIT 3;",
#         "description": "Test peaceful events",
#         "expected_behavior": "Should return Meditation and Yoga events, not Dance Party."
#     },
#     {
#         "query": "SELECT * FROM events WHERE answer(description, 'Is this a high-energy or lively event?') = 'Yes' LIMIT 3;",
#         "description": "Test high-energy events",
#         "expected_behavior": "Should return Dance Party only."
#     },
#     {
#         "query": "SELECT * FROM events WHERE answer(description, 'Does this event combine relaxation with physical activity?') = 'Yes' LIMIT 3;",
#         "description": "Test overlapping qualities",
#         "expected_behavior": "Should return Yoga event only."
#     },
#     {
#         "query": "SELECT * FROM events WHERE answer(description, 'Is this event focused on competitive gaming?') = 'Yes' LIMIT 3;",
#         "description": "Test irrelevant topic",
#         "expected_behavior": "Should return no events."
#     },
# ]

# # Execute test cases
# for i, test_case in enumerate(test_cases, 1):
#     print(f"Test Case {i}: {test_case['description']}")
#     print(f"Expected Behavior: {test_case['expected_behavior']}")
    
#     try:
#         result = suql_execute(
#             suql=test_case["query"],
#             table_w_ids=table_w_ids,
#             database=database,
#             fts_fields=fts_fields,
#             llm_model_name=llm_model_name,
#             disable_try_catch=disable_try_catch
#         )
#         print(f"Result: {result}")
#     except Exception as e:
#         print(f"Error: {e}")
#     print("-" * 50)
