import time
import re
import json


def extract_customer_attributes(customer_input, llm):
    start_time = time.time()
    ner_prompt = """Human: Find industry, size, Sustainability Focus, Inventory Manager, and the location in the 
    customer input. 
    Instructions: 
    - The Industry can be one of the following: Manufacturing, Warehousing, Government 
    and Public Safety, Education, Food and Beverage Distribution, Hospitality, Property Management, Retail, 
    or Other.
    - The Size can be one of the following: Individual Customer, Small Businesses (Smaller companies might prioritize 
    cost-effective solutions and fast shipping options), or Large Enterprises (Larger organizations may require more 
    comprehensive solutions, including strategic services like inventory management and safety consulting).
    - The Sustainability Focused true or false meaning environmentally conscious buyers: Customers interested in 
    sustainability solutions, looking for products that focus on energy management, water conservation, 
    waste reduction, and air quality improvement, or NOT Environmentally Conscious Buyers, 
    - The Inventory Manager true or false meaning a purchaser in large amounts to supply an organizational group, versus 
    an individual user purchasing for personal use. 
    
    The output must be in JSON format inside the tags <attributes></attributes>

    If the information on an entity is not available in the input then don't include that entity in the JSON output but 
    return the rest of the entities or empty tags <attributes></attributes>.

    Begin!

    Customer input: {customer_input}
    Assistant:""".format(customer_input=customer_input)

    entity_extraction_result = llm(ner_prompt).strip()

    result = re.search('<attributes>(.*?)</attributes>', entity_extraction_result, re.DOTALL)
    if result:
        attributes_str = result.group(1)
        attributes = json.loads(attributes_str)
        end_time = time.time()
        print("Time for extract_customer_attributes:", end_time - start_time)
        return attributes
    else:
        end_time = time.time()
        print("Time for extract_customer_attributes:", end_time - start_time)
        return {}
