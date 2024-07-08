# grainger_recommendations_chatbot

Note: incorporates ideas from https://github.com/aws-samples/amazon-bedrock-aistylist-lab/blob/main/README.md

Key modifications: 
  - Webscrape grainger.com for a potential list of related products.
  - Call internal Grainger Api for product details and compile data frame.
  - Webscrape sister company Zoro for the review data not on Grainger.com.
  - Call grainger.com directly to obtain product images
  - Uses Named Entity Recognition to categorize the customer and personalize the responses.
    - This could also be used for generating analytic data on use.
  
  - TODO: Address ordering capability.
      -   Provide an interface to add customer order history for later implementation within the Grainger VPC.
      -   Possibly orchestrate user login initially and thereby call order history and allow recommendations (e.g. clothing sizes) specific to the customer based on past orders.
      -   Implement an in-mobile-phone chat that uses the stored SQL database of past orders (currently for off-line searching by customer).
     
![Deer Hunting Hats](https://github.com/Noel-Niko/grainger_recommendations_chatbot/assets/83922762/b73cf069-c8fa-46bf-a45f-0d13e52651f8)

![Alaskan boots](https://github.com/Noel-Niko/grainger_recommendations_chatbot/assets/83922762/398ea974-43c4-476b-93e1-7a92fd52b5e8)

      

# Depth First Web Scrape to Obtain List of Related Products
![image](https://github.com/Noel-Niko/grainger_recommendations_chatbot/assets/83922762/f2fb3cad-5a00-448c-94e0-4a82eda0998b)

# Call to Obtain Product Details on All Valid Product Codes Collected
![dataframe](https://github.com/Noel-Niko/grainger_recommendations_chatbot/assets/83922762/aa974628-afae-428c-ae29-3b153b60132c)

# Generate Data Frame
![image](https://github.com/Noel-Niko/grainger_recommendations_chatbot/assets/83922762/179dc571-bf7f-4f86-93b8-9a8915c6b381)

# Enable Live-Calls to Obtain the Latest Product Recommendations from Zoro
![1VCE8](https://github.com/Noel-Niko/graigner_recommendations_chatbot/assets/83922762/d455c98e-e906-42b0-89e0-079e6c772bcd)


# AWS Bedrock
- LLM used: Anthropic
    ![img.png](img.png)
  
- AI Image Generator 
    ![img_1.png](img_1.png)

- For comparison: 
  - https://aws.amazon.com/bedrock/pricing/
  - https://openai.com/api/pricing/


## AI Image Generation:
- Though removed from the final product as superfluous, images can be generated of the products being used in the environment and by the type of user obtained from the gleaned customer attributes.
![img_3.png](img_3.png)
