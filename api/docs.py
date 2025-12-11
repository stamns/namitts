# api/docs.py - API文档生成
from flask_restx import Api, Resource, fields
# 初始化API文档（访问路径：/docs）
api = Api(
    app, 
    version='1.0', 
    title='纳米AI TTS API',
    description='语音合成API接口文档',
    doc='/docs/'  # 文档访问路径
)
# 定义请求模型（自动校验请求格式）
speech_model = api.model('SpeechRequest', {
    'text': fields.String(required=True, description='待合成文本'),
    'model': fields.String(required=True, description='声音模型ID'),
    'speed': fields.Float(default=1.0, description='语速（0.5-2.0）'),
    'emotion': fields.String(default='neutral', description='情绪（neutral/happy/sad/angry）')
})
# 注册接口到文档
ns = api.namespace('audio', description='音频合成接口')
@ns.route('/speech')
class SpeechAPI(Resource):
    @api.expect(speech_model)  # 关联请求模型
    @api.doc(security='apikey')  # 标记需要认证
    def post(self):
        """生成语音（支持长文本分段处理）"""
        return {"message": "语音生成中"}
