"use client";

import * as React from "react";
import { alpha } from "@mui/material/styles";
import Box from "@mui/material/Box";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableHead from "@mui/material/TableHead";
import TablePagination from "@mui/material/TablePagination";
import TableRow from "@mui/material/TableRow";
import TableSortLabel from "@mui/material/TableSortLabel";
import Toolbar from "@mui/material/Toolbar";
import Typography from "@mui/material/Typography";
import Paper from "@mui/material/Paper";
import Checkbox from "@mui/material/Checkbox";
import IconButton from "@mui/material/IconButton";
import Tooltip from "@mui/material/Tooltip";
import FormControlLabel from "@mui/material/FormControlLabel";
import Switch from "@mui/material/Switch";
import DeleteIcon from "@mui/icons-material/Delete";
import FilterListIcon from "@mui/icons-material/FilterList";
import { visuallyHidden } from "@mui/utils";
import CircleIcon from "@mui/icons-material/Circle";
import Stack from "@mui/material/Stack/Stack";
import ModeIcon from "@mui/icons-material/Mode";
import ClearIcon from "@mui/icons-material/Clear";
import Fade from "@mui/material/Fade/Fade";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import KeyboardArrowUpIcon from "@mui/icons-material/KeyboardArrowUp";
import NodePieChart, { PieData } from "./NodePieChart";
import Grid2 from "@mui/material/Unstable_Grid2"; // Grid version 2
import {
  Card,
  CardContent,
  Collapse,
  Container,
  FormGroup,
  useTheme,
} from "@mui/material";
import hexRgb from "hex-rgb";
import useMediaQuery from "@mui/material/useMediaQuery";
import { NodeStatus, TableData } from "@/data/nodeData";

interface HeadCell {
  disablePadding: boolean;
  id: keyof TableData;
  label: string;
  alignRight: boolean;
}

const headCells: readonly HeadCell[] = [
  {
    id: "name",
    alignRight: false,
    disablePadding: false,
    label: "DISPLAY NAME & ID",
  },
  {
    id: "status",
    alignRight: false,
    disablePadding: false,
    label: "STATUS",
  },
  {
    id: "last_seen",
    alignRight: false,
    disablePadding: false,
    label: "LAST SEEN",
  },
];

function descendingComparator<T>(a: T, b: T, orderBy: keyof T) {
  if (b[orderBy] < a[orderBy]) {
    return -1;
  }
  if (b[orderBy] > a[orderBy]) {
    return 1;
  }
  return 0;
}

type Order = "asc" | "desc";

function getComparator<Key extends keyof any>(
  order: Order,
  orderBy: Key,
): (
  a: { [key in Key]: number | string | boolean },
  b: { [key in Key]: number | string | boolean },
) => number {
  return order === "desc"
    ? (a, b) => descendingComparator(a, b, orderBy)
    : (a, b) => -descendingComparator(a, b, orderBy);
}

// Since 2020 all major browsers ensure sort stability with Array.prototype.sort().
// stableSort() brings sort stability to non-modern browsers (notably IE11). If you
// only support modern browsers you can replace stableSort(exampleArray, exampleComparator)
// with exampleArray.slice().sort(exampleComparator)
function stableSort<T>(
  array: readonly T[],
  comparator: (a: T, b: T) => number,
) {
  const stabilizedThis = array.map((el, index) => [el, index] as [T, number]);
  stabilizedThis.sort((a, b) => {
    const order = comparator(a[0], b[0]);
    if (order !== 0) {
      return order;
    }
    return a[1] - b[1];
  });
  return stabilizedThis.map((el) => el[0]);
}

interface EnhancedTableToolbarProps {
  selected: string | undefined;
  tableData: TableData[];
  onClear: () => void;
}
function EnhancedTableToolbar(props: EnhancedTableToolbarProps) {
  const { selected, onClear, tableData } = props;
  const theme = useTheme();
  const matches = useMediaQuery(theme.breakpoints.down("lg"));
  const isSelected = selected != undefined;
  const [debug, setDebug] = React.useState<boolean>(false);
  const debugSx = debug
    ? {
        "--Grid-borderWidth": "1px",
        borderTop: "var(--Grid-borderWidth) solid",
        borderLeft: "var(--Grid-borderWidth) solid",
        borderColor: "divider",
        "& > div": {
          borderRight: "var(--Grid-borderWidth) solid",
          borderBottom: "var(--Grid-borderWidth) solid",
          borderColor: "divider",
        },
      }
    : {};

  const pieData = React.useMemo(() => {
    const online = tableData.filter(
      (row) => row.status === NodeStatus.Online,
    ).length;
    const offline = tableData.filter(
      (row) => row.status === NodeStatus.Offline,
    ).length;
    const pending = tableData.filter(
      (row) => row.status === NodeStatus.Pending,
    ).length;

    return [
      { name: "Online", value: online, color: theme.palette.success.main },
      { name: "Offline", value: offline, color: theme.palette.error.main },
      { name: "Pending", value: pending, color: theme.palette.warning.main },
    ];
  }, [tableData]);

  const cardData = React.useMemo(() => {
    return pieData
      .filter((pieItem) => pieItem.value > 0)
      .concat({
        name: "Total",
        value: pieData.reduce((a, b) => a + b.value, 0),
        color: "#000000",
      });
  }, [pieData]);

  const cardStack = (
    <Stack
      sx={{ ...debugSx, paddingTop: 6 }}
      height={350}
      id="cardBox"
      display="flex"
      flexDirection="column"
      justifyContent="flex-start"
      flexWrap="wrap"
    >
      {cardData.map((pieItem) => (
        <Card
          key={pieItem.name}
          sx={{
            marginBottom: 2,
            marginRight: 2,
            width: 110,
            height: 110,
            backgroundColor: hexRgb(pieItem.color, {
              format: "css",
              alpha: 0.25,
            }),
          }}
        >
          <CardContent>
            <Typography
              variant="h4"
              component="div"
              gutterBottom={true}
              textAlign="center"
            >
              {pieItem.value}
            </Typography>
            <Typography
              sx={{ mb: 1.5 }}
              color="text.secondary"
              textAlign="center"
            >
              {pieItem.name}
            </Typography>
          </CardContent>
        </Card>
      ))}
    </Stack>
  );

  const selectedToolbar = (
    <Toolbar
      sx={{
        pl: { sm: 2 },
        pr: { xs: 1, sm: 1 },
        bgcolor: (theme) =>
          alpha(
            theme.palette.primary.main,
            theme.palette.action.activatedOpacity,
          ),
      }}
    >
      <Tooltip title="Clear">
        <IconButton onClick={onClear}>
          <ClearIcon />
        </IconButton>
      </Tooltip>
      <Typography
        sx={{ flex: "1 1 100%" }}
        color="inherit"
        style={{ fontSize: 18, marginBottom: 3, marginLeft: 3 }}
        component="div"
      >
        {selected} selected
      </Typography>
      <Tooltip title="Edit">
        <IconButton>
          <ModeIcon />
        </IconButton>
      </Tooltip>
    </Toolbar>
  );

  const unselectedToolbar = (
    <Toolbar
      sx={{
        pl: { sm: 2 },
        pr: { xs: 1, sm: 1 },
      }}
    >
      <Box sx={{ flex: "1 1 100%" }}></Box>
      <Tooltip title="Filter list">
        <IconButton>
          <FilterListIcon />
        </IconButton>
      </Tooltip>
    </Toolbar>
  );

  return (
    <Grid2 container spacing={1} sx={debugSx}>
      <Grid2 key="Header" xs={6}>
        <Typography
          sx={{ marginLeft: 3, marginTop: 1 }}
          variant="h6"
          id="tableTitle"
          component="div"
        >
          NODES
        </Typography>
      </Grid2>
      {/* Debug Controls */}
      <Grid2 key="Debug-Controls" xs={6} justifyContent="right" display="flex">
        <FormGroup>
          <FormControlLabel
            control={
              <Switch
                onChange={() => {
                  setDebug(!debug);
                }}
                checked={debug}
              />
            }
            label="Debug"
          />
        </FormGroup>
      </Grid2>

      {/* Pie Chart Grid */}
      <Grid2
        key="PieChart"
        md={6}
        xs={12}
        display="flex"
        justifyContent="center"
        alignItems="center"
      >
        <Box height={350} width={400}>
          <NodePieChart data={pieData} showLabels={matches} />
        </Box>
      </Grid2>

      {/* Card Stack Grid */}
      <Grid2
        key="CardStack"
        lg={6}
        display="flex"
        sx={{ display: { lg: "flex", xs: "none", md: "flex" } }}
      >
        {cardStack}
      </Grid2>

      {/*Toolbar Grid */}
      <Grid2 key="Toolbar" xs={12}>
        {isSelected ? selectedToolbar : unselectedToolbar}
      </Grid2>
    </Grid2>
  );
}

export interface NodeTableProps {
  tableData: TableData[];
}

interface EnhancedTableProps {
  onRequestSort: (
    event: React.MouseEvent<unknown>,
    property: keyof TableData,
  ) => void;
  order: Order;
  orderBy: string;
  rowCount: number;
}

function EnhancedTableHead(props: EnhancedTableProps) {
  const { order, orderBy, onRequestSort } = props;
  const createSortHandler =
    (property: keyof TableData) => (event: React.MouseEvent<unknown>) => {
      onRequestSort(event, property);
    };

  return (
    <TableHead>
      <TableRow>
        <TableCell id="dropdown"  colSpan={1} />
        {headCells.map((headCell) => (
          <TableCell
            key={headCell.id}
            align={headCell.alignRight ? "right" : "left"}
            padding={headCell.disablePadding ? "none" : "normal"}
            sortDirection={orderBy === headCell.id ? order : false}
          >
            <TableSortLabel
              active={orderBy === headCell.id}
              direction={orderBy === headCell.id ? order : "asc"}
              onClick={createSortHandler(headCell.id)}
            >
              {headCell.label}
              {orderBy === headCell.id ? (
                <Box component="span" sx={visuallyHidden}>
                  {order === "desc" ? "sorted descending" : "sorted ascending"}
                </Box>
              ) : null}
            </TableSortLabel>
          </TableCell>
        ))}
      </TableRow>
    </TableHead>
  );
}

function Row(props: {
  row: TableData;
  selected: string | undefined;
  setSelected: (a: string | undefined) => void;
}) {
  function renderStatus(status: NodeStatus) {
    switch (status) {
      case NodeStatus.Online:
        return (
          <Stack direction="row" alignItems="center" gap={1}>
            <CircleIcon color="success" style={{ fontSize: 15 }} />
            <Typography component="div" align="left" variant="body1">
              Online
            </Typography>
          </Stack>
        );

      case NodeStatus.Offline:
        return (
          <Stack direction="row" alignItems="center" gap={1}>
            <CircleIcon color="error" style={{ fontSize: 15 }} />
            <Typography component="div" align="left" variant="body1">
              Offline
            </Typography>
          </Stack>
        );
      case NodeStatus.Pending:
        return (
          <Stack direction="row" alignItems="center" gap={1}>
            <CircleIcon color="warning" style={{ fontSize: 15 }} />
            <Typography component="div" align="left" variant="body1">
              Pending
            </Typography>
          </Stack>
        );
    }
  }

  const { row, selected, setSelected } = props;
  const [open, setOpen] = React.useState(false);
  //const labelId = `enhanced-table-checkbox-${index}`;

  // Speed optimization. We compare string pointers here instead of the string content.
  const isSelected = selected == row.name;

  const handleClick = (event: React.MouseEvent<unknown>, name: string) => {
    if (isSelected) {
      setSelected(undefined);
    } else {
      setSelected(name);
    }
  };

  return (
    <React.Fragment>

      {/* Rendered Row */}
      <TableRow
        hover
        role="checkbox"
        aria-checked={isSelected}
        tabIndex={-1}
        key={row.name}
        selected={isSelected}
        sx={{ cursor: "pointer" }}
      >
        <TableCell  padding="none">
          <IconButton
            aria-label="expand row"
            size="small"
            onClick={() => setOpen(!open)}
          >
            {open ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
          </IconButton>
        </TableCell>
        <TableCell component="th" scope="row"   onClick={(event) => handleClick(event, row.name)}>
          <Stack>
            <Typography component="div" align="left" variant="body1">
              {row.name}
            </Typography>
            <Typography
              color="grey"
              component="div"
              align="left"
              variant="body2"
            >
              {row.id}
            </Typography>
          </Stack>
        </TableCell>
        <TableCell align="right" onClick={(event) => handleClick(event, row.name)}>{renderStatus(row.status)}</TableCell>
        <TableCell align="right" onClick={(event) => handleClick(event, row.name)}>
          <Typography component="div" align="left" variant="body1">
            {row.last_seen} days ago
          </Typography>
        </TableCell>
      </TableRow>

      {/* Row Expansion */}
      <TableRow>
        <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={6}>
          <Collapse in={open} timeout="auto" unmountOnExit>
            <Box sx={{ margin: 1 }}>
              <Typography variant="h6" gutterBottom component="div">
                History
              </Typography>
              <Table size="small" aria-label="purchases">
                <TableHead>
                  <TableRow>
                    <TableCell>Date</TableCell>
                    <TableCell>Customer</TableCell>
                    <TableCell align="right">Amount</TableCell>
                    <TableCell align="right">Total price ($)</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow key="test1">
                    <TableCell>Test1</TableCell>
                    <TableCell>Test2</TableCell>
                    <TableCell align="right">Test</TableCell>
                    <TableCell align="right">Test</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </Box>
          </Collapse>
        </TableCell>
      </TableRow>
    </React.Fragment>
  );
}

export default function NodeTable(props: NodeTableProps) {
  let { tableData } = props;

  const theme = useTheme();
  const is_xs = useMediaQuery(theme.breakpoints.only("xs"));

  const [order, setOrder] = React.useState<Order>("asc");
  const [orderBy, setOrderBy] = React.useState<keyof TableData>("status");
  const [selected, setSelected] = React.useState<string | undefined>(undefined);
  const [page, setPage] = React.useState(0);
  const [dense, setDense] = React.useState(false);
  const [rowsPerPage, setRowsPerPage] = React.useState(5);

  const handleRequestSort = (
    event: React.MouseEvent<unknown>,
    property: keyof TableData,
  ) => {
    const isAsc = orderBy === property && order === "asc";
    setOrder(isAsc ? "desc" : "asc");
    setOrderBy(property);
  };

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  // Avoid a layout jump when reaching the last page with empty rows.
  const emptyRows =
    page > 0 ? Math.max(0, (1 + page) * rowsPerPage - tableData.length) : 0;

  const visibleRows = React.useMemo(
    () =>
      stableSort(tableData, getComparator(order, orderBy)).slice(
        page * rowsPerPage,
        page * rowsPerPage + rowsPerPage,
      ),
    [order, orderBy, page, rowsPerPage, tableData],
  );

  return (
    <Box sx={{ width: "100%" }}>
      <Paper sx={{ width: "100%", mb: 2 }}>
        <EnhancedTableToolbar
          tableData={tableData}
          selected={selected}
          onClear={() => setSelected(undefined)}
        />
        <TableContainer>
          <Table
            sx={{ minWidth: 750 }}
            aria-labelledby="tableTitle"
            size={dense ? "small" : "medium"}
          >
            <EnhancedTableHead
              order={order}
              orderBy={orderBy}
              onRequestSort={handleRequestSort}
              rowCount={tableData.length}
            />
            <TableBody>
              {visibleRows.map((row, index) => {
                const labelId = `enhanced-table-checkbox-${index}`;

                return (
                  <Row
                    key={row.id}
                    row={row}
                    selected={selected}
                    setSelected={setSelected}
                  />
                );
              })}
              {emptyRows > 0 && (
                <TableRow
                  style={{
                    height: (dense ? 33 : 53) * emptyRows,
                  }}
                >
                  <TableCell colSpan={6} />
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
        {/* TODO: This creates the error Warning: Prop `id` did not match. Server: ":RspmmcqH1:" Client: ":R3j6qpj9H1:" */}
        <TablePagination
          rowsPerPageOptions={[5, 10, 25]}
          labelRowsPerPage={is_xs ? "Rows" : "Rows per page:"}
          component="div"
          count={tableData.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
        />
      </Paper>
    </Box>
  );
}
