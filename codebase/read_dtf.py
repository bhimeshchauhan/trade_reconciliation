import pandas as pd
import itertools
from easymoney.money import EasyPeasy

class read_dtf:

    def __init__(self, orderFile, confirmFile):
        # Completed order: orders that are fully executed
        self.completedOrder = []
        # Partial order: orders that are not fully executed
        self.partialOrder = []
        # Irregularities: erroneous execution/confirm
        self.irregularities = []
        # Left Execution: Partial Executions of Trade Orders that are left for next day
        self.leftExecution = {}
        # Vars for Currency and Calculation Inconsistencies
        self.exessive_execution_pos = []
        self.exessive_execution_neg = []
        self.exessive_execution_partial = []
        self.exessive_execution_wrongcurcalc = []
        self.exessive_execution_wrongtype = []

        # Business Analytics
        self.multiple_execution_list = []
        self.orderFile = orderFile
        self.confirmFile = confirmFile

    def __del__(self):
        return

    def multiple_execution(self):
        #  return: a List of order that is executed twice or more in file Trade_Confirm.
        #  Order $A$ was executed $times$ and $Quantity$ was executed while $Quantity$ was requested to be executed.
        #  $multiple_execution$ : [$orders$]

        dupdict = dupCon[dupCon.duplicated(subset='ISIN Code', keep=False)]
        # Dictionary of all the repeated trade orders including the duplicates.
        dupdictAll = dupdict.set_index('ISIN Code', verify_integrity=False, append=True).to_dict(orient='index')
        # Dictionary of all the repeated trade orders omitting the duplicates.
        dupdictOne = dupdict.set_index('ISIN Code').to_dict(orient='index')
        # Add trade orders to a list.
        for k, v in dupdictOne.items():
            self.multiple_execution_list.append(k)
            self.irregularities.append(k)
        return



    def exessive_execution(self):
        #  return: executed more than we ordered to.
        #  Order $A$ was executed for $Quantity$ amount while $Quantity$ was requested to be executed differing by $amount$.
        #  $excessive_execution$ : {
        #      "Quantity Executed" : $QuantityExecuted$,
        #      "Quantity Expected" : $QuantityExpected$,
        #      "Amount Difference" : $Amount$ # if -ve that means Quantity Executed > Quantity Expected
        #   }
        #   $excessive_execution_list$ : $statements for analysis$

        # Output Data Initialization
        excessive_execution = {}

        # Dictionary of Sum of all the repeated executed quantity of trade orders
        confirmExec = dupCon.groupby('ISIN Code')['Quantity Executed'].sum().reset_index()
        confirmExecOrder = dupCon.groupby('ISIN Code')['Quantity Order'].sum().reset_index()
        confirmExecDict = confirmExec.set_index('ISIN Code', verify_integrity=False, drop=True).to_dict(orient='index')

        # Dictionary of all the trade orders
        # NOTE:  Assuming that there are no repeats in the order file
        orderExec = order.groupby('ISIN')['ORDER QUANTITY'].sum().reset_index()
        orderExecDict = orderExec.set_index('ISIN').to_dict(orient='index')

        # For all orders in Trade_Orders File
        for orders in orderExecDict:


            # If order is present in Trade_Confirm file.
            if orders in confirmExecDict:
                # If Trade_Confirm execution is greater than Trade_Order order.
                if abs(confirmExecDict[orders]['Quantity Executed']) > abs(orderExecDict[orders]['ORDER QUANTITY']):
                    if orders not in self.irregularities:
                        excessive_execution[orders] = {}
                        excessive_execution[orders]["Quantity Executed"] = confirmExecDict[orders]['Quantity Executed']
                        excessive_execution[orders]["Quantity Expected"] = orderExecDict[orders]['ORDER QUANTITY']
                        excessive_execution[orders]["Amount Difference"] = orderExecDict[orders]['ORDER QUANTITY'] - \
                                                                           confirmExecDict[orders]['Quantity Executed']
                        self.irregularities.append(orders)
                        self.exessive_execution_pos.append("Order "+ orders + " was executed " +
                                                            str(excessive_execution[orders]["Quantity Executed"]) +
                                                            " times " + " while expected to be executed " +
                                                           str(excessive_execution[orders]["Quantity Expected"]) + " time.")


                # If Trade_Order order is greater than Trade_Confirm execution.
                elif abs(confirmExecDict[orders]['Quantity Executed']) < abs(orderExecDict[orders]['ORDER QUANTITY']):
                    excessive_execution[orders] = {}
                    excessive_execution[orders]["Quantity Executed"] = confirmExecDict[orders]['Quantity Executed']
                    excessive_execution[orders]["Quantity Expected"] = orderExecDict[orders]['ORDER QUANTITY']
                    excessive_execution[orders]["Amount Difference"] = orderExecDict[orders]['ORDER QUANTITY'] - \
                                                                       confirmExecDict[orders]['Quantity Executed']
                    # Append to partial order list
                    if orders not in self.partialOrder:
                        self.partialOrder.append(orders)
                        self.exessive_execution_partial.append("Order " + orders + " was partially executed " +
                                                       str(excessive_execution[orders]["Quantity Executed"]) +
                                                       " times " + " and needs to be executed " +
                                                        str(excessive_execution[orders]["Amount Difference"]) + " orders.")

                    # Append to amount left to execute list
                    if orders not in self.leftExecution.keys():
                        self.leftExecution[orders] = abs(orderExecDict[orders]['ORDER QUANTITY']) - \
                                                     abs(confirmExecDict[orders]['Quantity Executed'])

                # If Trade_Order order is equal to Trade_Confirm execution.
                elif abs(confirmExecDict[orders]['Quantity Executed']) == abs(orderExecDict[orders]['ORDER QUANTITY']):
                    # Append to completed order list
                    if orders not in self.completedOrder:
                        self.completedOrder.append(orders)


            # If order is not present in Trade_Confirm execution.
            else:
                # Add to irregularities list
                if orders not in self.irregularities:
                    self.irregularities.append(orders)
                    self.exessive_execution_neg.append("Order " + orders + " was not executed.")

        return

    def inconsistent_cost(self):
        #  return: inconsistent costs added
        #  Order $A$ was executed with different $amount$.
        #  $Names$ : {
        #      "Cost Executed" : $Cost Total$,
        #      "Reason" : $Reason$,
        #   }


        # Variables for Calculation
        ep = EasyPeasy()
        for orders in confirmsDict:
            #  Variables to be used in the method
            QtyExec = confirmsDict[orders]['Quantity Executed']
            QtyOrder = confirmsDict[orders]['Quantity Order']
            AvgPrice = confirmsDict[orders]['Average Price']
            Amount = confirmsDict[orders]['Amount']
            currCommission = confirmsDict[orders]['Cur. Comm.']
            currTotalAmount = confirmsDict[orders]['Cur. Net Amt.']
            currAmount = confirmsDict[orders]['Cur. Amt.']
            Commission = confirmsDict[orders]['Commission']
            tax = confirmsDict[orders]['Tax']
            otherCost = confirmsDict[orders]['Other Costs']
            totalAmount = confirmsDict[orders]['Total Net Amount']
            orderType = orderDict[orders[1]]['SIDE']
            confirmType = confirmsDict[orders]['Type']


            # Check for currency
            if (currAmount != (currCommission or currTotalAmount)):

                # Account for Exchange Rates
                newCommission = ep.currency_converter(amount=Commission, from_currency=currCommission, to_currency=currAmount)

                # If the Total Amount charged does not matches Total Charge accounting for orders on Trade_Orders Page.
                # If Total Amount charged does not matches Total Charge for orders executed Trade_Confirms Page.
                # If the Sub Amount on Trade_orders page is not equal to Sub Total.
                # If the Sub Amount on Trade_confirms page is not equal to Sub Total.
                if (abs(totalAmount) != abs((QtyOrder*AvgPrice) + newCommission + tax + otherCost)) or \
                        (abs(totalAmount) != abs((QtyExec*AvgPrice) + newCommission + tax + otherCost)) or \
                        (abs(Amount) != abs((QtyExec*AvgPrice))) or \
                        (abs(Amount) != abs((QtyOrder*AvgPrice))):
                    # Add to irregularities list
                    if orders[1] not in self.irregularities:
                        self.irregularities.append(orders[1])
                        self.exessive_execution_wrongcurcalc.append("Order " + orders[1] + " has inconsistent currency "
                                                        "but the total amount are not consistent with the calculation")

            # If we have same currency for Commission
            elif (currAmount == (currCommission and currTotalAmount)):

                # If the Total Amount charged does not matches Total Charge accounting for orders on Trade_Orders Page.
                # If Total Amount charged does not matches Total Charge for orders executed Trade_Confirms Page.
                # If the Sub Amount on Trade_orders page is not equal to Sub Total.
                # If the Sub Amount on Trade_confirms page is not equal to Sub Total.
                if (abs(totalAmount) != abs((QtyOrder*AvgPrice) + Commission + tax + otherCost)) or \
                        (abs(totalAmount) != abs((QtyExec*AvgPrice) + Commission + tax + otherCost)) or \
                        (abs(Amount) != abs((QtyExec*AvgPrice))) or \
                        (abs(Amount) != abs((QtyOrder*AvgPrice))):
                    # Add to irregularities list
                    if orders[1] not in self.irregularities:
                        self.irregularities.append(orders[1])
                        self.exessive_execution_wrongcurcalc.append("Order " + orders[1] + " has consistent currency "
                                                        "but the total amount are not consistent with the calculation")

                # If the amounts add up
                if (abs(totalAmount) == abs((QtyOrder * AvgPrice) + Commission + tax + otherCost)) and \
                        (abs(totalAmount) == abs((QtyExec * AvgPrice) + Commission + tax + otherCost)) and \
                        (abs(Amount) == abs((QtyExec * AvgPrice))) and \
                        (abs(Amount) == abs((QtyOrder * AvgPrice))):
                    # Add to completed order list
                    if orders[1] not in self.completedOrder:
                        self.completedOrder.append(orders[1])

            # If the Type (Sell/Buy) is not equal
            elif(orderType != confirmType):
                if orders[1] not in self.irregularities:
                    self.irregularities.append(orders[1])
                    self.exessive_execution_wrongtype.append("Order " + orders[1] + " was supposed to be of type"
                                                             + orderType + " while it was executed as " + confirmType)
        return


    def write_data(self):

        # Write Data
        data = [self.completedOrder, self.partialOrder, self.irregularities]
        pd.set_option('max_colwidth', 1000)
        df1 = pd.DataFrame((_ for _ in itertools.izip_longest(*data)),
                          columns=['Completed Order', 'Partial Order', 'Irregularities'])
        writer = pd.ExcelWriter('out/Trade_Reconciliation.xlsx', engine='xlsxwriter')
        df1.to_excel(writer, header=True, index=False, sheet_name='reconciliation')
        worksheet1 = writer.sheets['reconciliation']
        worksheet1.set_column(0, 2, 25)

        data2 = [self.multiple_execution_list,
                 self.exessive_execution_pos,
                 self.exessive_execution_neg,
                 self.exessive_execution_partial,
                 self.exessive_execution_wrongcurcalc,
                 self.exessive_execution_wrongtype]
        df2 = pd.DataFrame((_ for _ in itertools.izip_longest(*data2)),
                          columns=['Multiple Execution',
                                   'Excessive Execution',
                                   'Not Executed',
                                   'Partially Executed',
                                   'Inconsistent Currency & Calculation',
                                   'Inconsistent Sell/Buy Type'])
        df2.to_excel(writer, header=True, index=False, sheet_name='analytics')
        workbook = writer.book
        workbook.add_format({'text_wrap': True})
        worksheet2 = writer.sheets['analytics']
        worksheet2.set_column(0, 5, 95)
        writer.save()
        return

    def readData(self):

        # Assuming he columns name will always remain same
        global order
        global dupCon
        global orderDict
        global confirmsDict

        # Trade Ordered Dictionary
        order = pd.read_excel(self.orderFile,  usecols="B, D, E, F")
        orderDict = order.set_index('ISIN').to_dict(orient='index')

        # Confirm Trade Dictionary
        dupCon = pd.read_excel(self.confirmFile, usecols="B, D, E, F, G, H, I, J, K, M, N, O, P, Q, R, S")
        confirmsDict = dupCon.set_index('ISIN Code', verify_integrity=False, append=True).to_dict('index')

        # Call all the check function
        self.multiple_execution()
        self.exessive_execution()
        self.inconsistent_cost()
        self.write_data()

if __name__ == "__main__":
    orderPath = "res/Trade_Orders.xlsx"
    confirmPath = "res/Trade_Confirms.xlsx"
    read_dtf(orderPath, confirmPath).readData()