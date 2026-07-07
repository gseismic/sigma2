from __future__ import annotations


def test_root_package_reexports_core_and_common_signals():
    from sigma2 import (
        pyta2_signal,
        resolve_pyta2_indicator,
        rBookSpread,
        rGap,
        rKlineSignal,
        rPyta2SMA,
        rReturn,
        rSMA,
        rSignal,
        rTradeSignedVolume,
    )

    assert rSignal.__name__ == "rSignal"
    assert rKlineSignal.__name__ == "rKlineSignal"
    assert rReturn.__name__ == "rReturn"
    assert rGap.__name__ == "rGap"
    assert rSMA.__name__ == "rSMA"
    assert rPyta2SMA.__name__ == "rPyta2SMA"
    assert rBookSpread.__name__ == "rBookSpread"
    assert rTradeSignedVolume.__name__ == "rTradeSignedVolume"
    assert callable(pyta2_signal)
    assert callable(resolve_pyta2_indicator)


def test_core_exports_signal_base_classes_and_pyta2_base():
    from sigma2.core import (
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


def test_root_family_packages_export_concrete_signals():
    from sigma2.kline import rGap, rPyta2SMA, rReturn, rSMA
    from sigma2.kline.gap import rGap as rGapFromFile
    from sigma2.kline.pyta2 import rPyta2SMA as rPyta2SMAFromPackage
    from sigma2.kline.pyta2.sma import rPyta2SMA as rPyta2SMAFromFile
    from sigma2.kline.return_ import rReturn as rReturnFromFile
    from sigma2.kline.sma import rSMA as rSMAFromFile
    from sigma2.orderbook import rBookSpread
    from sigma2.orderbook.book_spread import rBookSpread as rBookSpreadFromFile
    from sigma2.trade import rTradeSignedVolume
    from sigma2.trade.trade_signed_volume import (
        rTradeSignedVolume as rTradeSignedVolumeFromFile,
    )

    assert rReturn is rReturnFromFile
    assert rGap is rGapFromFile
    assert rSMA is rSMAFromFile
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
