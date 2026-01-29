"""
Chart configuration builders.

Factory classes that convert declarative QuickChartDef definitions
into ChartConfig objects using snapshot data.
"""

from typing import Optional, TYPE_CHECKING
import pandas as pd

from domain.chart_config import ChartConfig, AxisConfig
from domain.quick_charts.definitions import (
    QuickChartDef,
    BarChartDef,
    BubbleChartDef,
    StatusChartDef,
)

if TYPE_CHECKING:
    from domain.snapshot import Snapshot


class ChartConfigBuilder:
    """
    Factory for building ChartConfig from QuickChartDef definitions.
    
    This class handles the conversion from declarative definitions
    to concrete configurations, including:
    - Filtering PIDs to those present in the snapshot
    - Extracting bar chart data from specific columns
    - Building bubble chart data from column patterns
    - Preprocessing status chart data
    """

    @classmethod
    def build(cls, definition: QuickChartDef, snapshot: "Snapshot") -> ChartConfig:
        """
        Build a ChartConfig from a QuickChartDef and snapshot data.
        
        Args:
            definition: The declarative chart definition
            snapshot: The loaded snapshot containing data and metadata
            
        Returns:
            A ChartConfig ready for rendering
        """
        if isinstance(definition, BarChartDef):
            return cls._build_bar_chart(definition, snapshot)
        elif isinstance(definition, BubbleChartDef):
            return cls._build_bubble_chart(definition, snapshot)
        elif isinstance(definition, StatusChartDef) and definition.source_column:
            return cls._build_parsed_status_chart(definition, snapshot)
        else:
            return cls._build_line_or_status_chart(definition, snapshot)

    @classmethod
    def _build_line_or_status_chart(
        cls, definition: QuickChartDef, snapshot: "Snapshot"
    ) -> ChartConfig:
        """Build a standard line or status chart configuration."""
        df = snapshot.snapshot
        
        # Resolve primary PIDs (filter to those present in data)
        primary_pids = cls._resolve_pids(definition, df)
        
        # Resolve secondary PIDs
        secondary_pids = [
            pid for pid in definition.secondary_pids 
            if pid in df.columns
        ]
        
        # Build axis configs
        primary_axis = AxisConfig(
            series=primary_pids,
            auto_scale=definition.primary_range is None,
            min_value=definition.primary_range[0] if definition.primary_range else None,
            max_value=definition.primary_range[1] if definition.primary_range else None,
            ticks=definition.primary_ticks,
            tick_labels=definition.primary_tick_labels,
        )
        
        secondary_axis = AxisConfig(
            series=secondary_pids,
            auto_scale=definition.secondary_range is None,
            min_value=definition.secondary_range[0] if definition.secondary_range else None,
            max_value=definition.secondary_range[1] if definition.secondary_range else None,
        )
        
        return ChartConfig(
            data=df,
            chart_type=definition.chart_type,
            primary_axis=primary_axis,
            secondary_axis=secondary_axis,
            title=definition.title,
            show_legend=definition.show_legend,
            pid_info=snapshot.pid_info,
            file_name=snapshot.file_name,
            date_time=snapshot.date_time,
            engine_hours=snapshot.hours,
            quick_chart_action_id=definition.action_id,
        )

    @classmethod
    def _build_bar_chart(
        cls, definition: BarChartDef, snapshot: "Snapshot"
    ) -> ChartConfig:
        """Build a bar chart from column values at Frame 0."""
        df = snapshot.snapshot
        
        # Get Frame 0 row
        frame_zero = df[df["Frame"] == 0]
        if frame_zero.empty:
            # Fall back to first row if Frame 0 not found
            frame_zero = df.iloc[[0]]
        
        # Extract values from source columns
        values = []
        for col in definition.source_columns:
            if col in frame_zero.columns:
                try:
                    val = float(frame_zero[col].iloc[0])
                    if definition.convert_seconds_to_hours:
                        val = round(val / 3600, 2)
                    values.append(val)
                except (ValueError, IndexError, TypeError):
                    values.append(0.0)
            else:
                values.append(0.0)
        
        # Create DataFrame for bar chart
        chart_data = pd.DataFrame({
            definition.x_label or "Category": definition.bar_labels,
            definition.y_label: values,
        })
        
        return ChartConfig(
            data=chart_data,
            chart_type="bar",
            primary_axis=AxisConfig(
                series=[definition.y_label],
                auto_scale=True,
            ),
            secondary_axis=AxisConfig(series=[]),
            title=definition.title,
            x_column=definition.x_label or "Category",
            x_label=definition.x_label,
            pid_info=snapshot.pid_info,
            file_name=snapshot.file_name,
            date_time=snapshot.date_time,
            engine_hours=snapshot.hours,
            quick_chart_action_id=definition.action_id,
        )

    @classmethod
    def _build_bubble_chart(
        cls, definition: BubbleChartDef, snapshot: "Snapshot"
    ) -> ChartConfig:
        """Build a bubble chart from column pattern data."""
        df = snapshot.snapshot
        
        # Get total reference value for percentage calculation
        total_value = 1.0
        if definition.total_reference_column:
            if definition.total_reference_column in df.columns:
                try:
                    total_value = float(df[definition.total_reference_column].iloc[0])
                except (ValueError, IndexError, TypeError):
                    total_value = 1.0
        
        # Build data from column pattern
        rows = []
        for col in df.columns:
            if definition.column_pattern:
                # Extract indices from column name matching pattern
                # Pattern like "EUD_Spdload_blm_timer_nvv[{x},{y}]"
                prefix = definition.column_pattern.split("{")[0]
                if col.startswith(prefix) and "[" in col:
                    try:
                        indices_str = col.split("[")[1].rstrip("]")
                        indices = indices_str.split(",")
                        x_idx = int(indices[0])
                        y_idx = int(indices[1])
                        
                        # Get value
                        timer_value = float(df[col].iloc[0])
                        
                        # Calculate percentage
                        if total_value > 0:
                            percent = (timer_value / total_value) * 100
                        else:
                            percent = 0
                        
                        # Map indices to actual values
                        x_val = definition.x_index_map.get(x_idx, x_idx) if definition.x_index_map else x_idx
                        y_val = definition.y_index_map.get(y_idx, y_idx) if definition.y_index_map else y_idx
                        
                        rows.append({
                            definition.x_label: x_val,
                            definition.y_label: y_val,
                            definition.size_label: percent,
                        })
                    except (IndexError, ValueError):
                        continue
        
        # Create DataFrame and filter out zero values
        chart_data = pd.DataFrame(rows)
        if not chart_data.empty:
            chart_data = chart_data[chart_data[definition.size_label] > 0]
        
        return ChartConfig(
            data=chart_data,
            chart_type="bubble",
            primary_axis=AxisConfig(
                series=[definition.y_label],
                auto_scale=True,
            ),
            secondary_axis=AxisConfig(series=[]),
            title=definition.title,
            x_column=definition.x_label,
            x_label=definition.x_label,
            bubble_size_column=definition.size_label,
            bubble_size_scale=50.0,
            pid_info=snapshot.pid_info,
            file_name=snapshot.file_name,
            date_time=snapshot.date_time,
            engine_hours=snapshot.hours,
            quick_chart_action_id=definition.action_id,
        )

    @classmethod
    def _build_parsed_status_chart(
        cls, definition: StatusChartDef, snapshot: "Snapshot"
    ) -> ChartConfig:
        """
        Build a status chart by parsing a multi-digit status column.
        
        The source column contains strings like "00101" where each digit
        represents a different status flag.
        """
        df = snapshot.snapshot.copy()
        col_name = definition.source_column
        
        if col_name not in df.columns:
            # Return empty chart if column missing
            return cls._build_line_or_status_chart(definition, snapshot)
        
        # Parse the string of digits into individual columns
        s = df[col_name].astype(str)
        split_df = pd.DataFrame(s.map(list).tolist(), index=df.index)
        split_df = split_df.apply(pd.to_numeric, errors="coerce").fillna(0).astype(int)
        
        # Determine how many columns we can label
        num_cols = min(
            len(definition.digit_labels) if definition.digit_labels else 0,
            split_df.shape[1]
        )
        
        # Create display columns
        new_pids = []
        prefix = definition.display_prefix or ""
        
        for i in range(num_cols):
            label = definition.digit_labels[i]
            display_col = f"{prefix}_{label}" if prefix else label
            df[display_col] = split_df.iloc[:, i]
            new_pids.append(display_col)
        
        # Build as status chart with generated PIDs
        return ChartConfig(
            data=df,
            chart_type="status",
            primary_axis=AxisConfig(series=new_pids, auto_scale=True),
            secondary_axis=AxisConfig(series=[]),
            title=definition.title,
            show_legend=definition.show_legend,
            pid_info=snapshot.pid_info,
            file_name=snapshot.file_name,
            date_time=snapshot.date_time,
            engine_hours=snapshot.hours,
            quick_chart_action_id=definition.action_id,
        )

    @classmethod
    def _resolve_pids(cls, definition: QuickChartDef, df: pd.DataFrame) -> list[str]:
        """
        Resolve PIDs to those actually present in the DataFrame.
        
        Handles dynamic_primary_pids for cases like variable cylinder counts.
        """
        # Use dynamic PIDs if specified, otherwise use primary_pids
        candidate_pids = definition.dynamic_primary_pids or definition.primary_pids
        
        # Filter to PIDs present in the data
        return [pid for pid in candidate_pids if pid in df.columns]
