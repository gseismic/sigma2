from __future__ import annotations


def test_root_package_reexports_canonical_signals():
    import sigma2
    from sigma2 import (
        KlineATR,
        KlineBoll,
        KlineGap,
        KlineKDJ,
        KlineMA,
        KlineMACD,
        KlineRSI,
        KlineReturn,
        forward_signal_apply,
        pyta2_signal,
        rBookSpread,
        rKlineATR,
        rKlineATRBoundTrigger,
        rKlineBoll,
        rKlineFutureChange,
        rKlineFutureHighLowChange,
        rKlineFutureReturn,
        rKlineGap,
        rKlineKDJ,
        rKlineMA,
        rKlineMACD,
        rKlineRSI,
        rKlineReturn,
        rKlineSignal,
        rSignal,
        rTradeSignedVolume,
        resolve_pyta2_indicator,
    )

    assert rSignal.__name__ == "rSignal"
    assert rKlineSignal.__name__ == "rKlineSignal"
    assert rKlineMA.__name__ == "rKlineMA"
    assert rKlineRSI.__name__ == "rKlineRSI"
    assert rKlineMACD.__name__ == "rKlineMACD"
    assert rKlineBoll.__name__ == "rKlineBoll"
    assert rKlineKDJ.__name__ == "rKlineKDJ"
    assert rKlineATR.__name__ == "rKlineATR"
    assert rKlineReturn.__name__ == "rKlineReturn"
    assert rKlineGap.__name__ == "rKlineGap"
    assert rKlineFutureReturn.__name__ == "rKlineFutureReturn"
    assert rKlineFutureChange.__name__ == "rKlineFutureChange"
    assert rKlineFutureHighLowChange.__name__ == "rKlineFutureHighLowChange"
    assert rKlineATRBoundTrigger.__name__ == "rKlineATRBoundTrigger"
    assert rBookSpread.__name__ == "rBookSpread"
    assert rTradeSignedVolume.__name__ == "rTradeSignedVolume"
    assert callable(pyta2_signal)
    assert callable(forward_signal_apply)
    assert all(
        callable(function)
        for function in (
            KlineMA,
            KlineRSI,
            KlineMACD,
            KlineBoll,
            KlineKDJ,
            KlineATR,
            KlineReturn,
            KlineGap,
        )
    )
    assert callable(resolve_pyta2_indicator)

    deprecated = {
        "ATR",
        "Boll",
        "KDJ",
        "MA",
        "MACD",
        "RSI",
        "rATR",
        "rBoll",
        "rGap",
        "rKDJ",
        "rMA",
        "rMACD",
        "rPyta2SMA",
        "rRSI",
        "rReturn",
        "rSMA",
    }
    assert deprecated.isdisjoint(sigma2.__all__)


def test_core_exports_signal_base_classes_and_pyta2_base():
    from sigma2.core import (
        forward_signal_apply,
        pyta2_signal,
        rKlineSignal,
        rKlineWindowSignal,
        rOrderBookSignal,
        rPyta2Signal,
        rSignal,
        rTradeSignal,
    )

    assert rSignal.__name__ == "rSignal"
    assert rKlineSignal.__name__ == "rKlineSignal"
    assert rKlineWindowSignal.__name__ == "rKlineWindowSignal"
    assert rOrderBookSignal.__name__ == "rOrderBookSignal"
    assert rTradeSignal.__name__ == "rTradeSignal"
    assert rPyta2Signal.__name__ == "rPyta2Signal"
    assert callable(pyta2_signal)
    assert callable(forward_signal_apply)


def test_kline_categories_export_single_canonical_implementation():
    import sigma2.kline as kline
    from sigma2.kline.momentum import (
        KlineKDJ,
        KlineRSI,
        rKlineKDJ,
        rKlineRSI,
    )
    from sigma2.kline.momentum.kdj import rKlineKDJ as rKlineKDJFromFile
    from sigma2.kline.momentum.rsi import rKlineRSI as rKlineRSIFromFile
    from sigma2.kline.price import (
        KlineGap,
        KlineReturn,
        rKlineGap,
        rKlineReturn,
    )
    from sigma2.kline.price.gap import rKlineGap as rKlineGapFromFile
    from sigma2.kline.price.return_ import rKlineReturn as rKlineReturnFromFile
    from sigma2.kline.trend import (
        KlineMA,
        KlineMACD,
        rKlineMA,
        rKlineMACD,
    )
    from sigma2.kline.trend.ma import rKlineMA as rKlineMAFromFile
    from sigma2.kline.trend.macd import rKlineMACD as rKlineMACDFromFile
    from sigma2.kline.volatility import (
        KlineATR,
        KlineBoll,
        rKlineATR,
        rKlineBoll,
    )
    from sigma2.kline.volatility.atr import rKlineATR as rKlineATRFromFile
    from sigma2.kline.volatility.boll import rKlineBoll as rKlineBollFromFile

    assert (rKlineMA, rKlineMACD) == (rKlineMAFromFile, rKlineMACDFromFile)
    assert (rKlineRSI, rKlineKDJ) == (rKlineRSIFromFile, rKlineKDJFromFile)
    assert (rKlineATR, rKlineBoll) == (rKlineATRFromFile, rKlineBollFromFile)
    assert (rKlineReturn, rKlineGap) == (rKlineReturnFromFile, rKlineGapFromFile)
    assert (
        kline.rKlineMA,
        kline.rKlineMACD,
        kline.rKlineRSI,
        kline.rKlineKDJ,
        kline.rKlineATR,
        kline.rKlineBoll,
        kline.rKlineReturn,
        kline.rKlineGap,
    ) == (
        rKlineMA,
        rKlineMACD,
        rKlineRSI,
        rKlineKDJ,
        rKlineATR,
        rKlineBoll,
        rKlineReturn,
        rKlineGap,
    )
    assert all(
        callable(function)
        for function in (
            KlineMA,
            KlineMACD,
            KlineRSI,
            KlineKDJ,
            KlineATR,
            KlineBoll,
            KlineReturn,
            KlineGap,
        )
    )
    assert rKlineMA.__module__ == "sigma2.kline.trend.ma"
    assert rKlineRSI.__module__ == "sigma2.kline.momentum.rsi"
    assert rKlineATR.__module__ == "sigma2.kline.volatility.atr"
    assert rKlineReturn.__module__ == "sigma2.kline.price.return_"


def test_target_package_is_canonical_and_effect_paths_forward():
    from sigma2.kline.effect import (
        rKlineATRBoundTrigger as old_rKlineATRBoundTrigger,
    )
    from sigma2.kline.effect import rKlineFutureReturn as old_rKlineFutureReturn
    from sigma2.kline.target import (
        rKlineATRBoundTrigger,
        rKlineFutureChange,
        rKlineFutureHighLowChange,
        rKlineFutureReturn,
    )
    from sigma2.kline.target.bound_trigger import (
        rKlineATRBoundTrigger as rKlineATRBoundTriggerFromFile,
    )
    from sigma2.kline.target.future_change import (
        rKlineFutureChange as rKlineFutureChangeFromFile,
    )
    from sigma2.kline.target.future_high_low_change import (
        rKlineFutureHighLowChange as rKlineFutureHighLowChangeFromFile,
    )
    from sigma2.kline.target.future_return import (
        rKlineFutureReturn as rKlineFutureReturnFromFile,
    )

    assert rKlineATRBoundTrigger is rKlineATRBoundTriggerFromFile
    assert rKlineFutureChange is rKlineFutureChangeFromFile
    assert rKlineFutureHighLowChange is rKlineFutureHighLowChangeFromFile
    assert rKlineFutureReturn is rKlineFutureReturnFromFile
    assert old_rKlineATRBoundTrigger is rKlineATRBoundTrigger
    assert old_rKlineFutureReturn is rKlineFutureReturn
    assert rKlineATRBoundTrigger.__module__ == "sigma2.kline.target.bound_trigger"
    assert rKlineFutureChange.__module__ == "sigma2.kline.target.future_change"
    assert (
        rKlineFutureHighLowChange.__module__
        == "sigma2.kline.target.future_high_low_change"
    )
    assert rKlineFutureReturn.__module__ == "sigma2.kline.target.future_return"


def test_market_family_packages_export_concrete_signals():
    from sigma2.orderbook import rBookSpread
    from sigma2.orderbook.book_spread import rBookSpread as rBookSpreadFromFile
    from sigma2.trade import rTradeSignedVolume
    from sigma2.trade.trade_signed_volume import (
        rTradeSignedVolume as rTradeSignedVolumeFromFile,
    )

    assert rBookSpread is rBookSpreadFromFile
    assert rTradeSignedVolume is rTradeSignedVolumeFromFile


def test_pyta2_utils_expose_resolver_registry_and_import_helper():
    from sigma2.utils.pyta2 import (
        ensure_pyta2_importable,
        register_pyta2_indicator,
        resolve_pyta2_indicator,
    )

    assert callable(ensure_pyta2_importable)
    assert callable(register_pyta2_indicator)
    assert resolve_pyta2_indicator("SMA").__name__ == "rSMA"
