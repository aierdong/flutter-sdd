#!/usr/bin/env python3
"""使用商品列表的示例，检查 sdd-roadmap 路线图的正反场景。"""

import importlib.util
from pathlib import Path
import unittest


MODULE_PATH = Path(__file__).with_name('sdd_lint.py')
MODULE_SPEC = importlib.util.spec_from_file_location('roadmap_lint', MODULE_PATH)
lint = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(lint)


def document(route='p99', slices=None, order=None, extra=None, agreements=None,
             sign_status='未验收', sign_record=None, status='draft',
             way='用户手工走一遍', who='用户', goal='用户能创建商品列表页，完成一次增删改查并看到列表保持最新',
             scope='- 不做批量导入。理由：本次只验证单条记录的增删改查',
             void='', placeholder=''):
    """独立生成一份路线图。参数默认是可通过的形状，负例只改一处。"""
    if slices is None:
        slices = [
            {'slug': 'product-list', '编号': 'p99-001', '解决什么问题': '用户看不到已有商品',
             '做完后用户能': '用户打开列表页并看到全部商品', '前置': '无', '状态': '未开始'},
            {'slug': 'product-edit', '编号': 'p99-002', '解决什么问题': '用户改不了商品信息',
             '做完后用户能': '用户修改一条商品后看到列表更新',
             '前置': '001（提供：可浏览的商品列表）', '状态': '未开始'},
        ]
    if order is None:
        order = '001 → 002'

    body = []
    for item in slices:
        body.append('#### 切片：%s' % item.get('名称', item['slug']))
        for key in lint.SLICE_KEYS:
            if key in item:
                body.append('- %s：%s' % (key, item[key]))
        body.append('')
    slice_text = '\n'.join(body)

    if extra is None:
        extra_text = '- 路线外增补：无'
    else:
        extra_text = '\n'.join([
            '#### 增补：%s' % extra.get('名称', '调整列表页布局'),
            '- 编号：%s' % extra.get('编号', 'p99-001'),
            '- 附属于：%s' % extra.get('附属于', '001'),
            '- 关系：调整列表页的布局并增加骨架屏',
            '- 登记：%s' % extra.get('登记', '是'),
            '- 验证：不单独安排，整体验收时只列举',
        ])

    if agreements is None:
        agreement_text = '本次没有跨切片约定'
    else:
        agreement_text = '\n'.join([
            '#### 约定：错误提示统一',
            '- 要求：新增和修改失败时给出同一套提示',
            '- 覆盖切片：%s' % agreements.get('覆盖切片', '001, 002'),
            '- 留给各切片 plan 决定：提示文案的具体位置',
        ])

    record = ''
    if sign_record is not None:
        record = '\n'.join([
            '',
            '#### 整体验收记录',
            '- 时间：2026-01-01 10:00',
            '- 执行者：用户',
            '- 实际路径：打开列表页，修改一条商品，回到列表确认已更新',
            '- 结果：%s' % sign_record.get('结果', '通过'),
            '- 未通过处：%s' % sign_record.get('未通过处', '-'),
        ])

    text = '\n'.join([
        '# 商品管理路线图',
        '',
        '- 路线图：%s' % route,
        '- 大需求：商品列表的增删改查',
        '- Status：%s' % status,
        '- 版本：v1',
        '',
        '## 1. 整体目标与边界',
        '',
        '**整体目标**：%s' % goal,
        '',
        '**整体不做**：',
        '',
        scope,
        '',
        '## 2. 整体完成条件',
        '',
        '- 完成条件：用户在不刷新页面的情况下完成一条商品的新增、修改和删除',
        '- 操作路径：打开列表页 → 新增一条商品 → 修改它的名称 → 删除它 → 列表恢复原样',
        '- 验证方式：%s' % way,
        '- 验证者：%s' % who,
        '',
        '## 3. 切片清单',
        '',
        slice_text,
        '',
        extra_text,
        '',
        '## 4. 依赖与顺序',
        '',
        '- 推进顺序：%s' % order,
        '- 顺序理由：先让用户能看到列表，再让用户能改数据',
        '',
        '## 5. 跨切片约定',
        '',
        agreement_text,
        '',
        '## 6. 决策记录',
        '',
        '#### 决定：按用户动作切片',
        '- 决定：切片按用户能完成的一件事划分，还是按技术层次划分',
        '- 选择：按用户动作划分，每片都能单独交付',
        '- 放弃：按数据层、接口层、界面层划分',
        '- 何时重新评估：某一片需要独立的技术前置时',
        '',
        '## 7. 整体验收记录',
        '',
        '- 状态：%s' % sign_status,
        record,
        void,
        placeholder,
        '',
    ])
    return 'specs/%s-product-roadmap.md' % route, text


class RoadmapLintTest(unittest.TestCase):
    def check(self, path=None, text=None, **kwargs):
        path, built = document(**kwargs)
        rep = lint.Report()
        lint.check_document(rep, built if text is None else text, path)
        return rep

    def assert_only(self, code, **kwargs):
        rep = self.check(**kwargs)
        self.assertTrue(rep.failures, '这一组应当失败，实际全部通过')
        for failure in rep.failures:
            self.assertTrue(failure.startswith(code), '期望 %s，实际 %s' % (code, failure))
        return rep

    def test_valid_document_passes(self):
        rep = self.check()
        self.assertEqual([], rep.failures)
        self.assertEqual(lint.TOTAL_RULES, len(rep.checked))

    def test_head_status_must_be_known(self):
        self.assert_only('L01', status='done')

    def test_route_must_match_file_name(self):
        path, text = document()
        rep = lint.Report()
        lint.check_document(rep, text, 'specs/p98-product-roadmap.md')
        self.assertTrue(any(item.startswith('L01') for item in rep.failures))

    def test_goal_must_be_a_process(self):
        self.assert_only('L03', goal='商品管理')

    def test_scope_out_needs_reason(self):
        self.assert_only('L03', scope='- 不做批量导入')

    def test_verify_way_must_be_known(self):
        self.assert_only('L04', way='跑一下测试')

    def test_verifier_must_be_known(self):
        self.assert_only('L04', who='系统')

    def test_slice_needs_every_field(self):
        slices = [{'slug': 'product-list', '编号': 'p99-001',
                   '解决什么问题': '用户看不到已有商品', '前置': '无', '状态': '未开始'}]
        self.assert_only('L05', slices=slices, order='001')

    def test_slug_must_be_unique(self):
        slices = [
            {'slug': 'product-list', '编号': 'p99-001', '解决什么问题': '看不到商品',
             '做完后用户能': '看到列表', '前置': '无', '状态': '未开始'},
            {'slug': 'product-list', '编号': 'p99-002', '解决什么问题': '改不了商品',
             '做完后用户能': '改一条商品', '前置': '001（提供：列表）', '状态': '未开始'},
        ]
        rep = self.check(slices=slices)
        self.assertTrue(any('slug' in item for item in rep.failures))

    def test_numbers_must_be_continuous(self):
        slices = [
            {'slug': 'product-list', '编号': 'p99-002', '解决什么问题': '看不到商品',
             '做完后用户能': '看到列表', '前置': '无', '状态': '未开始'},
        ]
        self.assert_only('L06', slices=slices, order='002')

    def test_order_must_match_numbers(self):
        self.assert_only('L06', order='002 → 001')

    def test_require_must_exist(self):
        slices = [
            {'slug': 'product-list', '编号': 'p99-001', '解决什么问题': '看不到商品',
             '做完后用户能': '看到列表', '前置': '007（提供：某能力）', '状态': '未开始'},
        ]
        self.assert_only('L07', slices=slices, order='001')

    def test_require_needs_capability(self):
        slices = [
            {'slug': 'product-list', '编号': 'p99-001', '解决什么问题': '看不到商品',
             '做完后用户能': '看到列表', '前置': '无', '状态': '未开始'},
            {'slug': 'product-edit', '编号': 'p99-002', '解决什么问题': '改不了商品',
             '做完后用户能': '改一条商品', '前置': '001', '状态': '未开始'},
        ]
        rep = self.check(slices=slices)
        self.assertTrue(any('提供' in item for item in rep.failures))

    def test_cycle_is_reported(self):
        slices = [
            {'slug': 'product-list', '编号': 'p99-001', '解决什么问题': '看不到商品',
             '做完后用户能': '看到列表', '前置': '002（提供：改后的数据）', '状态': '未开始'},
            {'slug': 'product-edit', '编号': 'p99-002', '解决什么问题': '改不了商品',
             '做完后用户能': '改一条商品', '前置': '001（提供：列表）', '状态': '未开始'},
        ]
        rep = self.check(slices=slices)
        self.assertTrue(any('成环' in item for item in rep.failures))

    def test_extra_and_none_line_conflict(self):
        path, text = document()
        block = '\n'.join([
            '#### 增补：调整布局',
            '- 编号：p99-001',
            '- 附属于：001',
            '- 关系：调整列表页的布局并增加骨架屏',
            '- 登记：是',
            '- 验证：不单独安排，整体验收时只列举',
            '',
        ])
        text = text.replace('- 路线外增补：无', block + '- 路线外增补：无')
        rep = lint.Report()
        lint.check_document(rep, text, path)
        self.assertTrue(any(item.startswith('L08') for item in rep.failures))

    def test_extra_owner_must_exist(self):
        self.assert_only('L08', extra={'附属于': '009'})

    def test_extra_allows_shared_number(self):
        rep = self.check(extra={'编号': 'p99-001'})
        self.assertEqual([], rep.failures)

    def test_agreement_cover_must_exist(self):
        self.assert_only('L09', agreements={'覆盖切片': '001, 008'})

    def test_signed_off_needs_record(self):
        self.assert_only('L10', sign_status='已验收')

    def test_signed_off_pass_needs_dash(self):
        self.assert_only('L10', sign_status='已验收',
                         sign_record={'结果': '通过', '未通过处': '第三步'})

    def test_signed_off_fail_needs_gap(self):
        self.assert_only('L10', sign_status='已验收',
                         sign_record={'结果': '未通过', '未通过处': '-'})

    def test_unverified_with_record_is_contradiction(self):
        self.assert_only('L10', sign_record={'结果': '通过'})

    def test_placeholder_left_behind(self):
        self.assert_only('L11', placeholder='- 补充：<待填>')

    def test_void_words(self):
        self.assert_only('L11', void='- 后续：稍后补上')


if __name__ == '__main__':
    unittest.main()
