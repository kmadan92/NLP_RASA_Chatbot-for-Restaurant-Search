from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from rasa_sdk import Action
from rasa_sdk.events import SlotSet
import zomatopy
import json
import smtplib
from email.message import EmailMessage

class ActionSearchRestaurants(Action):
	def name(self):
		return 'action_search_restaurants'
		
	def run(self, dispatcher, tracker, domain):
		config={ "user_key":"5d75770145af17fd5ff82a76025d5940"}
		zomato = zomatopy.initialize_app(config)
		loc = tracker.get_slot('location')
		cuisine = tracker.get_slot('cuisine')
		price = tracker.get_slot('price')
		
		#find budget boundary
		minBudget, maxBudget = getMinMaxBudget(price);
		location_detail=zomato.get_location(loc, 1)
		
		d1 = json.loads(location_detail)
		lat=d1["location_suggestions"][0]["latitude"]
		lon=d1["location_suggestions"][0]["longitude"]
		cuisines_dict={'bakery':5,'chinese':25,'cafe':30,'italian':55,'biryani':7,'north indian':50,'south indian':85}
		results=zomato.restaurant_search("", lat, lon, str(cuisines_dict.get(cuisine)), 50)
		
		json_results = json.loads(results)
		
		#filter by budget
		temp_dict={}
		final_dict={}
		if json_results['results_found'] == 0:
			response= "no results"
		else:
			i=0
			for restaurant in json_results['restaurants']:
				temp_dict=[restaurant['restaurant']["user_rating"]["aggregate_rating"],restaurant['restaurant']['name'],restaurant['restaurant']['location']['address'], restaurant['restaurant']['average_cost_for_two']]
				if (temp_dict[3] >= minBudget) and (temp_dict[3] <= maxBudget):						
					final_dict[i] = temp_dict
					i=i+1
		
		#sort by rating
		sorted_dict={}
		for k, v in sorted(final_dict.items(), key=lambda item: item[1][0], reverse=True):
			sorted_dict[k]=v
		
		#prepare top 5 response
		response=""
		if len(sorted_dict) == 0:
			response= "no results"
		else:
			i=0;
			for k, v in sorted_dict.items():
				i=i+1
				response=response+ "Found "+ v[1]+ " in "+ v[2]+ "where price for two people is Rs." +str(v[3]) +"and rating is " +str(v[0])+"..."+"\n"
				if (i == 5):
					break;
		
		dispatcher.utter_message("-----"+response)
		
		return [SlotSet('location',loc)]
		

class ActionSendEmail(Action):
	def name(self):
		return 'action_send_email'
		
	def run(self, dispatcher, tracker, domain):
		config={ "user_key":"5d75770145af17fd5ff82a76025d5940"}
		zomato = zomatopy.initialize_app(config)
		loc = tracker.get_slot('location')
		cuisine = tracker.get_slot('cuisine')
		price = tracker.get_slot('price')
		location_detail=zomato.get_location(loc, 1)
		
		d1 = json.loads(location_detail)
		lat=d1["location_suggestions"][0]["latitude"]
		lon=d1["location_suggestions"][0]["longitude"]
		cuisines_dict={'bakery':5,'chinese':25,'cafe':30,'italian':55,'biryani':7,'north indian':50,'south indian':85}
		results=zomato.restaurant_search("", lat, lon, str(cuisines_dict.get(cuisine)), 50)
		
		#find out budget boundary
		minBudget, maxBudget = getMinMaxBudget(price);
		
		json_result = json.loads(results)
		
		#filter by budget
		temp_dict={}
		final_dict={}
		if json_result['results_found'] == 0:
			response= "no results"
		else:
			i=0
			for restaurant in json_result['restaurants']:
				temp_dict=[restaurant['restaurant']["user_rating"]["aggregate_rating"],restaurant['restaurant']['name'],restaurant['restaurant']['location']['address'], restaurant['restaurant']['average_cost_for_two']]
				if (temp_dict[3] >= minBudget) and (temp_dict[3] <= maxBudget):						
					final_dict[i] = temp_dict
					i=i+1
		
		#sort by rating
		sorted_dict={}
		for k, v in sorted(final_dict.items(), key=lambda item: item[1][0], reverse=True):
			sorted_dict[k]=v
		
		
		#prepare response to send mail.
		email = tracker.get_slot('email')
		response_email=""
		if len(sorted_dict) == 0:
			response_email= "no results"
		else:
			i=0;
			for k, v in sorted_dict.items():
				i=i+1
				response_email=response_email+ "Found "+ v[1]+ " in "+ v[2]+ "where price for two people is Rs." +str(v[3]) +"and rating is " +str(v[0])+"..."+"\n"
				if (i == 10):
					break;
		sender_email = ''
		reciever_email= email
		password = ''
		message = response_email
			
		server = smtplib.SMTP('smtp.gmail.com', 587)
		server.starttls()
		server.login(sender_email, password)
		server.sendmail(sender_email, reciever_email, message)
		
		dispatcher.utter_message("Email sent")
		
		return email

def getMinMaxBudget(price):
    minBudget = 0
    maxBudget = 5000;
    
    if price == 'Lesser than Rs. 300':
        maxBudget = 300
    elif price == 'Rs. 300 to 700':
        minBudget = 300
        maxBudget = 700
    else:
        minBudget = 700
    return [minBudget, maxBudget]
