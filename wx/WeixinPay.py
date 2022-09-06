from weixin.pay import WeixinPay, WeixinPayError, FAIL
from weixin.base import Map, WeixinError

class WeixinPayHH(WeixinPay):

    def transfers(self, **data):
        """
        申请退款
        out_trade_no、transaction_id至少填一个且
        out_refund_no、total_fee、refund_fee、op_user_id为必填参数
        appid、mchid、nonce_str不需要填入
        """
        if not self.key or not self.cert:
            raise WeixinError("企业付款口需要双向证书")
        url = "https://api.mch.weixin.qq.com/mmpaymkttransfers/promotion/transfers"

        data['check_name'] = 'NO_CHECK'
        data['desc'] = '提现'
        

        if "partner_trade_no" not in data:
            raise WeixinPayError("企业付款口中，缺少必填参数partner_trade_no")
        if "openid" not in data:
            raise WeixinPayError("企业付款口中，缺少必填参数openid")
        if "amount" not in data:
            raise WeixinPayError("企业付款口中，缺少必填参数amount")
        # if "desc" not in data:
        #     raise WeixinPayError("企业付款口中，缺少必填参数desc")


        return self._fetch(url, data, True, True)

    def transfersForBank(self, **data):
        """
        申请退款
        out_trade_no、transaction_id至少填一个且
        out_refund_no、total_fee、refund_fee、op_user_id为必填参数
        appid、mchid、nonce_str不需要填入
        """
        if not self.key or not self.cert:
            raise WeixinError("企业付款口需要双向证书")
        url = "https://api.mch.weixin.qq.com/mmpaymkttransfers/promotion/transfers"

        data['check_name'] = 'NO_CHECK'
        data['desc'] = '提现'

        if "partner_trade_no" not in data:
            raise WeixinPayError("企业付款口中，缺少必填参数partner_trade_no")
        if "enc_bank_no" not in data:
            raise WeixinPayError("企业付款口中，缺少必填参数enc_bank_no")
        if "enc_true_name" not in data:
            raise WeixinPayError("企业付款口中，缺少必填参数enc_true_name")
        if "bank_code" not in data:
            raise WeixinPayError("企业付款口中，缺少必填参数bank_code")
        if "amount" not in data:
            raise WeixinPayError("企业付款口中，缺少必填参数amount")
        # if "desc" not in data:
        #     raise WeixinPayError("企业付款口中，缺少必填参数desc")

        return self._fetch(url, data, True, True)



    def _fetch(self, url, data, use_cert=False, is_cash=False):
        if is_cash:
            data.setdefault("mch_appid", self.app_id)
            data.setdefault("mchid", self.mch_id)
        else:
            data.setdefault("appid", self.app_id)
            data.setdefault("mch_id", self.mch_id)
        data.setdefault("nonce_str", self.nonce_str)
        data.setdefault("sign", self.sign(data))

        if use_cert:
            resp = self.sess.post(url, data=self.to_xml(data), cert=(self.cert, self.key))
        else:
            resp = self.sess.post(url, data=self.to_xml(data))
        content = resp.content.decode("utf-8")
        if "return_code" in content:
            data = Map(self.to_dict(content))
            if data.return_code == FAIL:
                raise WeixinPayError(data.return_msg)
            if "result_code" in content and data.result_code == FAIL:
                raise WeixinPayError(data.err_code_des)
            return data
        return content
        