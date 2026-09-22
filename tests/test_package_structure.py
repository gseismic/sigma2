from __future__ import annotations


def test_root_package_reexports_core_and_common_signals():
    from sigma2 import (
        ATR,
        Boll,
        KDJ,
        MA,
        MACD,
        RSI,
        forward_signal_apply,
        pyta2_signal,
        resolve_pyta2_indicator,
        rBookSpread,
        rATR,
        rBoll,
        rGap,
        rKDJ,
        rKlineATRBoundTrigger,
        rKlineFutureChange,
        rKlineFutureHighLowChange,
        rKlineFutureReturn,
        rKlineSignal,
        rMA,
        rMACD,
        rPyta2SMA,
        rReturn,
        rRSI,
        rSMA,
        rSignal,
        rTradeSignedVolume,
    )

    assert rSignal.__name__ == "rSignal"
    assert rMA.__name__ == "rMA"
    assert rRSI.__name__ == "rRSI"
    assert rMACD.__name__ == "rMACD"
    assert rBoll.__name__ == "rBoll"
    assert rKDJ.__name__ == "rKDJ"
    assert rATR.__name__ == "rATR"
    assert rKlineSignal.__name__ == "rKlineSignal"
    assert rKlineFutureReturn.__name__ == "rKlineFutureReturn"
    assert rKlineFutureChange.__name__ == "rKlineFutureChange"
    assert rKlineFutureHighLowChange.__name__ == "rKlineFutureHighLowChange"
    assert rKlineATRBoundTrigger.__name__ == "rKlineATRBoundTrigger"
    assert rReturn.__name__ == "rReturn"
    assert rGap.__name__ == "rGap"
    assert rSMA.__name__ == "rSMA"
    assert rPyta2SMA.__name__ == "rPyta2SMA"
    assert rBookSpread.__name__ == "rBookSpread"
    assert rTradeSignedVolume.__name__ == "rTradeSignedVolume"
    assert callable(pyta2_signal)
    assert callable(forward_signal_apply)
    assert all(callable(function) for function in (MA, RSI, MACD, Boll, KDJ, ATR))
    assert callable(resolve_pyta2_indicator)


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


def test_root_family_packages_export_concrete_signals():
    from sigma2.kline import (
        ATR,
        Boll,
        KDJ,
        MA,
        MACD,
        RSI,
        rATR,
        rBoll,
        rGap,
        rKDJ,
        rKlineATRBoundTrigger,
        rKlineFutureChange,
        rKlineFutureHighLowChange,
        rKlineFutureReturn,
        rMA,
        rMACD,
        rPyta2SMA,
        rReturn,
        rRSI,
        rSMA,
    )
    from sigma2.kline.effect import rKlineATRBoundTrigger as rKlineATRBoundTriggerFromPackage
    from sigma2.kline.effect import rKlineFutureReturn as rKlineFutureReturnFromPackage
    from sigma2.kline.effect.bound_trigger import (
        rKlineATRBoundTrigger as rKlineATRBoundTriggerFromFile,
    )
    from sigma2.kline.effect.future_change import rKlineFutureChange as rKlineFutureChangeFromFile
    from sigma2.kline.effect.future_high_low_change import (
        rKlineFutureHighLowChange as rKlineFutureHighLowChangeFromFile,
    )
    from sigma2.kline.effect.future_return import rKlineFutureReturn as rKlineFutureReturnFromFile
    from sigma2.kline.gap import rGap as rGapFromFile
    from sigma2.kline.pyta2 import rPyta2SMA as rPyta2SMAFromPackage
    from sigma2.kline.pyta2.sma import rPyta2SMA as rPyta2SMAFromFile
    from sigma2.kline.return_ import rReturn as rReturnFromFile
    from sigma2.kline.sma import rSMA as rSMAFromFile
    from sigma2.kline.atr import ATR as ATRFromFile, rATR as rATRFromFile
    from sigma2.kline.boll import Boll as BollFromFile, rBoll as rBollFromFile
    from sigma2.kline.kdj import KDJ as KDJFromFile, rKDJ as rKDJFromFile
    from sigma2.kline.ma import MA as MAFromFile, rMA as rMAFromFile
    from sigma2.kline.macd import MACD as MACDFromFile, rMACD as rMACDFromFile
    from sigma2.kline.rsi import RSI as RSIFromFile, rRSI as rRSIFromFile
    from sigma2.orderbook import rBookSpread
    from sigma2.orderbook.book_spread import rBookSpread as rBookSpreadFromFile
    from sigma2.trade import rTradeSignedVolume
    from sigma2.trade.trade_signed_volume import (
        rTradeSignedVolume as rTradeSignedVolumeFromFile,
    )

    assert rReturn is rReturnFromFile
    assert (MA, RSI, MACD, Boll, KDJ, ATR) == (
        MAFromFile,
        RSIFromFile,
        MACDFromFile,
        BollFromFile,
        KDJFromFile,
        ATRFromFile,
    )
    assert (rMA, rRSI, rMACD, rBoll, rKDJ, rATR) == (
        rMAFromFile,
        rRSIFromFile,
        rMACDFromFile,
        rBollFromFile,
        rKDJFromFile,
        rATRFromFile,
    )
    assert rGap is rGapFromFile
    assert rSMA is rSMAFromFile
    assert rKlineFutureReturn is rKlineFutureReturnFromPackage
    assert rKlineFutureReturn is rKlineFutureReturnFromFile
    assert rKlineFutureChange is rKlineFutureChangeFromFile
    assert rKlineFutureHighLowChange is rKlineFutureHighLowChangeFromFile
    assert rKlineATRBoundTrigger is rKlineATRBoundTriggerFromPackage
    assert rKlineATRBoundTrigger is rKlineATRBoundTriggerFromFile
    assert rPyta2SMA is rPyta2SMAFromPackage
    assert rPyta2SMA is rPyta2SMAFromFile
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
