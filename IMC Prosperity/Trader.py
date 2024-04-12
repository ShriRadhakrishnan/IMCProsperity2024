from typing import List
import jsonpickle
from datamodel import OrderDepth, UserId, TradingState, Order



class Trader:
    def __init__(self):
        # Initialize variables for SMA calculation for STARFRUIT
        self.starfruit_10_price_history = []
        self.starfruit_100_price_history = []
        self.prev_sma_10_starfruit = None
        self.prev_sma_100_starfruit = None
        self.prev_10_sum = 0
        self.prev_100_sum = 0


    def calculate_sma(self, prices, period):
        """Calculate the Simple Moving Average."""
        if len(prices) >= period:
            return sum(prices[-period:]) / period
        return None

    def detect_crossover(self, current_sma_10, current_sma_100):
        """Detects SMA crossover events."""
        if self.prev_sma_10_starfruit is not None and self.prev_sma_100_starfruit is not None:
            if (current_sma_10 >= current_sma_100) and ((current_sma_10 - current_sma_100) > (self.prev_sma_10_starfruit - self.prev_sma_100_starfruit)):
                return "LONG_ENTRY"
            elif (current_sma_10 >= current_sma_100) and ((current_sma_10 - current_sma_100) < (self.prev_sma_10_starfruit - self.prev_sma_100_starfruit)):
                return "LONG_EXIT"
            elif (current_sma_10 <= current_sma_100) and ((current_sma_100 - current_sma_10) > (self.prev_sma_100_starfruit - self.prev_sma_10_starfruit)):
                return "SHORT_ENTRY"
            elif (current_sma_10 <= current_sma_100) and ((current_sma_100 - current_sma_10) < (self.prev_sma_100_starfruit - self.prev_sma_10_starfruit)):
                return "SHORT_EXIT"
        return "NO_CROSSOVER"
    

    def calculate_mid_price(self, order_depth: OrderDepth):

        bid_weighted_average = sum([price * quantity for price, quantity in order_depth.buy_orders.items()]) / sum(order_depth.buy_orders.values())
        ask_weighted_average = sum([price * quantity for price, quantity in order_depth.sell_orders.items()]) / sum(order_depth.sell_orders.values())
        mid_price = (bid_weighted_average + ask_weighted_average) / 2
        return int(mid_price)


    def run(self, state: TradingState):
        
        if state.traderData:
            previous_state = jsonpickle.decode(state.traderData)
            self.starfruit_10_price_history = previous_state.get("starfruit_10_price_history", [])
            self.starfruit_100_price_history = previous_state.get("starfruit_100_price_history", [])
            self.prev_sma_10_starfruit = previous_state.get("prev_sma_10_starfruit", None)
            self.prev_sma_100_starfruit = previous_state.get("prev_sma_100_starfruit", None)
            self.prev_10_sum = previous_state.get("prev_10_sum", 0)
            self.prev_100_sum = previous_state.get("prev_100_sum", 0)
        else:
            # If there's no traderData, initialize with defaults
            self.starfruit_10_price_history = []
            self.starfruit_100_price_history = []
            self.prev_sma_10_starfruit = None
            self.prev_sma_100_starfruit = None
            self.prev_10_sum = 0
            self.prev_100_sum = 0


        result = {}
        for product in state.order_depths:

            #Implement the scalping strategy for AMETHYSTS
            if product == "AMETHYSTS":
                order_depth: OrderDepth = state.order_depths[product]
                orders: List[Order] = []
                acceptable_price = 10000  # Participant should calculate this value
        
                if len(order_depth.sell_orders) != 0:
                    best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]
                    if int(best_ask) < acceptable_price:
                        orders.append(Order(product, best_ask, -best_ask_amount))
        
                if len(order_depth.buy_orders) != 0:
                    best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]
                    if int(best_bid) > acceptable_price:
                        orders.append(Order(product, best_bid, -best_bid_amount))
                result[product] = orders
            

        #Implement the SMA strategy for STARFRUIT
            if product == "STARFRUIT":
                order_depth: OrderDepth = state.order_depths[product]
                orders: List[Order] = []

                mid_price_starfruit = self.calculate_mid_price(order_depth)

                self.starfruit_10_price_history.append(mid_price_starfruit)
                self.starfruit_100_price_history.append(mid_price_starfruit)

                if len(self.starfruit_100_price_history) > 100:
                    sma_100 = (self.prev_100_sum - self.starfruit_100_price_history[0] + mid_price_starfruit) / 100
                else:
                    sma_100 = None
                if (len(self.starfruit_10_price_history) > 10):
                    sma_10 = (self.prev_10_sum - self.starfruit_10_price_history[0] + mid_price_starfruit) / 10
                else:
                    sma_10 = None

            
                if sma_10 and sma_100:
                    crossover_signal = self.detect_crossover(sma_10, sma_100)
                    if crossover_signal == "LONG_ENTRY":
                        # Buy at the lowest available ask price
                        best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]
                        orders.append(Order(product, best_ask, -best_ask_amount))
                    elif crossover_signal == "LONG_EXIT":
                        # Sell at the highest available bid price
                        best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]
                        orders.append(Order(product, best_bid, best_bid_amount))

                    elif crossover_signal == "SHORT_ENTRY":
                        # Sell at the highest available bid price

                        best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]
                        orders.append(Order(product, best_bid, best_bid_amount))

                    elif crossover_signal == "SHORT_EXIT":
                        # Buy at the lowest available ask price

                        best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]
                        orders.append(Order(product, best_ask, -best_ask_amount))



                result[product] = orders
                self.prev_10_sum += mid_price_starfruit
                self.prev_100_sum += mid_price_starfruit

                if len(self.starfruit_100_price_history) > 100:
                    self.prev_100_sum -= self.starfruit_100_price_history.pop(0)

                if len(self.starfruit_10_price_history) > 10:
                    self.prev_10_sum -= self.starfruit_10_price_history.pop(0)
                

                self.prev_sma_10_starfruit = sma_10
                self.prev_sma_100_starfruit = sma_100

            
        traderData = jsonpickle.encode({
            "starfruit_10_price_history": self.starfruit_10_price_history,
            "starfruit_100_price_history": self.starfruit_100_price_history,
            "prev_10_sum": self.prev_10_sum,
            "prev_100_sum": self.prev_100_sum,
            "prev_sma_10_starfruit": self.prev_sma_10_starfruit,
            "prev_sma_100_starfruit": self.prev_sma_100_starfruit,
        })

        conversions = 1
        return result, conversions, traderData