# -*- coding: utf-8 -*-

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_model.ui import SimpleCard
from ask_sdk_model.slu.entityresolution.status_code import StatusCode

import boto3

# log
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

sb = SkillBuilder()

@sb.request_handler(can_handle_func=is_request_type('LaunchRequest'))
def launch_request_handler(handler_input):
    logger.info('LaunchRequest handler called!!')
    speech_text = 'どの都道府県のB級グルメが知りたいですか？'
    return handler_input.response_builder.speak(speech_text).set_card(
        SimpleCard('どの都道府県？', speech_text)).set_should_end_session(
        False).response


@sb.request_handler(can_handle_func=is_intent_name('BudgetFriendlyGourmetIntent'))
def budget_friendly_gourmet_intent_handler(handler_input):
    logger.info('BudgetFriendlyGourmetIntent handler called!!')
    slots = handler_input.request_envelope.request.intent.slots
    slot_name = 'Prefecture'
    gourmet_info = None
    # 呼びかけられた都道府県名からB級グルメ情報を取得する
    if slot_name in slots:
        prefecture_slot = slots[slot_name]
        logger.info('Slot [{Prefecture}] found! Slot: %s', 
            prefecture_slot)
        # [A] インテントスロットに都道府県名が設定されているかをチェックする
        slot_resolution_list = prefecture_slot.resolutions.resolutions_per_authority
        slot_resolution = slot_resolution_list[0]
        slot_status = slot_resolution.status.code
        if StatusCode.ER_SUCCESS_MATCH == slot_status:
            # [B] インテントスロットからスロット値のIDを取得し、B級グルメ情報を取得する
            prefecture_id = slot_resolution.values[0].value.id
            logger.info('Prefecture id: %s', prefecture_id)
            try:
                gourmet_info = get_budget_friendly_gourmet_for(prefecture_id)
            except Exception:
                pass
    # [C] グルメ情報を基に読み上げるセリフを組み立てる
    if gourmet_info is not None:
        speech_text = '{}には{}というB級グルメがあります。{}です。'.format(
            prefecture_slot.value,
            gourmet_info['yomi'],
            gourmet_info['detail']
        )
        end_session = True  # B級グルメ情報を返す場合はスキルのセッションは完了させる
    else:
        logger.info('No gourmet info found...')
        speech_text = 'もう一度、都道府県名を教えてください。'
        end_session = False # 聞き返すのでスキルのセッションは継続させる
    # 読み上げるセリフを返す
    return handler_input.response_builder.speak(speech_text).set_card(
        SimpleCard('B級グルメ', speech_text)).set_should_end_session(
        end_session).response


def get_budget_friendly_gourmet_for(prefecture):
    '''
    都道府県のB級グルメ説明を取得する
    存在しない場合はNoneを返す。
    '''
    logger.info('get_budget_friendly_gourmet_for method called!! [Prefecture:%s]', prefecture)
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('BudgetFriendlyGourmet')
        response = table.get_item(
            Key={
                'prefecture': prefecture
            }
        )
        result = None
        item = response.get('Item', None)
        if item:
            result = item 
        return result
    except Exception as e:
        logger.error('Exception at get_budget_friendly_gourmet_for: %s', e)
        raise e


@sb.request_handler(
    can_handle_func=lambda input:
        is_intent_name('AMAZON.CancelIntent')(input) or
        is_intent_name('AMAZON.StopIntent')(input))
def cancel_and_stop_intent_handler(handler_input):
    logger.info('CancelIntent or StopIntent handler called!!')
    speech_text = 'またね！'
    return handler_input.response_builder.speak(speech_text).response


@sb.request_handler(can_handle_func=is_request_type('SessionEndedRequest'))
def session_ended_request_handler(handler_input):
    logger.info('SessionEndedRequest handler called!!')
    return handler_input.response_builder.response


@sb.exception_handler(can_handle_func=lambda i, e: True)
def all_exception_handler(handler_input, exception):
    logger.info('All Exception handler called!!')
    logger.error('Encountered following exception: {}'.format(exception))
    speech = '処理中にエラーが発生しました。もう一度試してください。'
    handler_input.response_builder.speak(speech).ask(speech)
    return handler_input.response_builder.response


# Handler to be provided in lambda console.
handler = sb.lambda_handler()
