/*
 * Copyright 2020 Free Software Foundation, Inc.
 *
 * This file is part of GNU Radio
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 *
 */

/* This file is automatically generated using bindtool */

#include <pybind11/pybind11.h>
#include <pybind11/complex.h>
#include <pybind11/stl.h>

namespace py = pybind11;

#include <gnuradio/analog/agc2_ff.h>

void bind_agc2_ff(py::module& m)
{
    using agc2_ff    = gr::analog::agc2_ff;


    py::class_<agc2_ff,gr::sync_block,
        std::shared_ptr<agc2_ff>>(m, "agc2_ff")

        .def(py::init(&agc2_ff::make),
           py::arg("attack_rate") = 0.10000000000000001, 
           py::arg("decay_rate") = 0.01, 
           py::arg("reference") = 1., 
           py::arg("gain") = 1. 
        )
        

        .def("attack_rate",&agc2_ff::attack_rate)
        .def("decay_rate",&agc2_ff::decay_rate)
        .def("reference",&agc2_ff::reference)
        .def("gain",&agc2_ff::gain)
        .def("max_gain",&agc2_ff::max_gain)
        .def("set_attack_rate",&agc2_ff::set_attack_rate,
            py::arg("rate") 
        )
        .def("set_decay_rate",&agc2_ff::set_decay_rate,
            py::arg("rate") 
        )
        .def("set_reference",&agc2_ff::set_reference,
            py::arg("reference") 
        )
        .def("set_gain",&agc2_ff::set_gain,
            py::arg("gain") 
        )
        .def("set_max_gain",&agc2_ff::set_max_gain,
            py::arg("max_gain") 
        )
        .def("to_basic_block",[](std::shared_ptr<agc2_ff> p){
            return p->to_basic_block();
        })
        ;


} 