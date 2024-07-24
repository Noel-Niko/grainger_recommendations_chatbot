import json
import re
import time


def split_process_and_message_from_response(recs_response):
    start_time = time.time()
    recs_response = recs_response.strip()

    message_match = re.search("<response>(.*?)</response>", recs_response, re.DOTALL)
    message = message_match.group(1).strip() if message_match else None

    if "<products>" in recs_response and "</products>" in recs_response:
        json_content = recs_response[recs_response.index("<products>") + len("<products>") : recs_response.index("</products>")].strip()

        try:
            parsed_response = json.loads(json_content)

            if isinstance(parsed_response, list):
                products_list = []
                for product_info in parsed_response:
                    product_data = {"product": product_info.get("product", ""), "code": product_info.get("code", "")}
                    products_list.append(product_data)

                response_json = {"products": products_list}
                end_time = time.time()
                print("Time for split_process_and_message_from_response:", end_time - start_time)
                return message, response_json
            else:
                print("Error: Unexpected format of parsed response")
                end_time = time.time()
                print("Time for split_process_and_message_from_response:", end_time - start_time)
                return None, None

        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {str(e)}")
            end_time = time.time()
            print("Time for split_process_and_message_from_response:", end_time - start_time)
            return None, None
    else:
        print("Error: Unexpected format of recs_response")
        end_time = time.time()
        print("Time for split_process_and_message_from_response:", end_time - start_time)
        return None, None
