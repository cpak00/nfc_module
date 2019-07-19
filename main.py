import operateCard as card

filename = input('请输入文件名(csv格式:卡号,初始金额):')
print('请按照提示卡号批量刷卡')

card.quantity_new_card(filename)

a = input('按任意键结束')