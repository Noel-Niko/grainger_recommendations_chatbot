# grainger_recommendations_chatbot

PROJECT IN DEVELOPMENT

Plan: mimic https://github.com/aws-samples/amazon-bedrock-aistylist-lab/blob/main/README.md

Key modifications: 
  - webscrape grainger.com for list of products and descriptions creating a limited base of content.
  - webscrape sister company for the missing review data
  - call grainger.com directly to obtain product images and use stability.stable-diffusion-xl-v1 only for enhanced content
  - provide interface to add customer order history for later implementation within the grainger vpc
  - TODO: plan for addressing ordering capability.
    - -   Possibly orchestrate user login initially and thereby call order history and allow placing orders.
      -   Implement an in-mobile-phone chat that uses the stored SQL database to serve past orders (currently stored for off-line use), which are most closely related to the current search.


    

![1VCE8](https://github.com/Noel-Niko/graigner_recommendations_chatbot/assets/83922762/d455c98e-e906-42b0-89e0-079e6c772bcd)
