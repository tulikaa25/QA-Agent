# Checkout Feature Specifications

## Pricing and Discounts
Rule D-1 Valid Code The discount code SAVE15 must apply a 15% reduction to the Subtotal value
Rule D-2 Invalid Code Any code other than SAVE15 must result in a 000 discount
Rule D-3 Final Calculation Total Due equals Subtotal minus Discount plus Shipping Cost

## Shipping Costs
Rule S-1 Standard The Standard shipping option ship_standard has a cost of 000
Rule S-2 Express The Express shipping option ship_express has a cost of 1000

## Cart Item Rules
Rule C-1 Add Item Clicking the Add Automation Pro Kit button #add_item_P002_btn must add a new line item P002 to the cart and increase the subtotal by 5000
Rule C-2 Add Item Clicking the Add Performance Tester button #add_item_P003_btn must add a new line item P003 to the cart and increase the subtotal by 10000

## Form Validation
Rule V-1 Required Fields The Full Name #name_input Email #email_input and Address #address_input fields are required and cannot be empty
Rule V-2 Email Format The Email field #email_input must contain exactly one @ symbol at least one character after the @ and at least two characters after the final dot e.g. .co or .com
Rule V-3 Pay Button State The Pay Now button #pay_now_btn must remain disabled until all required fields satisfy Rules V-1 and V-2

## Success State
Rule T-1 Final Action Upon clicking the enabled Pay Now button the paragraph with ID #payment_status must become visible

